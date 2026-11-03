#!/usr/bin/env python3
"""
mcp-whatsapp-bridge — Model Context Protocol (MCP) Server for WhatsApp Automation.
Enables Claude Desktop, Claude Code, and autonomous AI agents to dispatch direct WhatsApp messages,
alerts, media, and status reports to personal or team WhatsApp numbers without expensive third-party Twilio APIs.
Supports both local gateway bridges and direct HTTP webhook routing.
"""

import os
import sys
import json
import urllib.request
import urllib.error
import urllib.parse
import time
import argparse
from typing import Optional, Dict, Any, Tuple

try:
    from mcp.server.mcpserver import MCPServer
    app = MCPServer("whatsapp-bridge-mcp")
except ImportError:
    app = None

def get_bridge_config() -> Tuple[str, str, str]:
    gateway_url = os.environ.get("WHATSAPP_GATEWAY_URL", "http://localhost:3001/send")
    api_key = os.environ.get("WHATSAPP_API_KEY", "")
    default_recipient = os.environ.get("WHATSAPP_DEFAULT_PHONE", "")
    return gateway_url, api_key, default_recipient

def clean_phone_number(raw_phone: str) -> str:
    """Normalize phone number: strip +, spaces, hyphens, parentheses."""
    return raw_phone.replace("+", "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "").strip()

def dispatch_http_request(url: str, payload: Dict[str, Any], api_key: str = "", timeout: int = 15) -> Tuple[bool, Dict[str, Any], str]:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return True, data, ""
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="ignore")
        return False, {}, f"HTTP {e.code}: {err}"
    except Exception as e:
        return False, {}, str(e)

def send_whatsapp_message_impl(phone_number: str, message: str) -> str:
    gateway_url, api_key, default_phone = get_bridge_config()
    target_phone = phone_number or default_phone
    if not target_phone:
        return "Error: No destination phone number provided and WHATSAPP_DEFAULT_PHONE is not set."

    cleaned_phone = clean_phone_number(target_phone)
    payload = {
        "to": cleaned_phone,
        "message": message
    }
    
    ok, data, err = dispatch_http_request(gateway_url, payload, api_key)
    if ok:
        status = data.get("status", "sent")
        return f"Successfully delivered WhatsApp message to {cleaned_phone} (Status: {status})."
    return f"Failed to send WhatsApp message via bridge ({gateway_url}): {err}"

def send_whatsapp_media_impl(phone_number: str, media_url: str, caption: Optional[str] = None, media_type: str = "image") -> str:
    gateway_url, api_key, default_phone = get_bridge_config()
    target_phone = phone_number or default_phone
    if not target_phone:
        return "Error: No destination phone number provided and WHATSAPP_DEFAULT_PHONE is not set."

    cleaned_phone = clean_phone_number(target_phone)
    media_url_endpoint = gateway_url
    if gateway_url.endswith("/send"):
        media_url_endpoint = gateway_url[:-5] + "/send-media"

    payload = {
        "to": cleaned_phone,
        "media_url": media_url,
        "caption": caption or "",
        "media_type": media_type
    }
    
    ok, data, err = dispatch_http_request(media_url_endpoint, payload, api_key)
    if ok:
        status = data.get("status", "sent")
        return f"Successfully delivered {media_type} to {cleaned_phone} (Status: {status})."
    return f"Failed to send WhatsApp media via bridge ({media_url_endpoint}): {err}"

def send_whatsapp_alert_impl(alert_title: str, details: str, urgency: str = "NORMAL") -> str:
    _, _, default_phone = get_bridge_config()
    if not default_phone:
        return "Error: WHATSAPP_DEFAULT_PHONE is not configured in the environment."
        
    prefix = "🚨 *[CRITICAL ALERT]*" if urgency.upper() == "CRITICAL" else "📢 *[AGENT NOTIFICATION]*"
    formatted = f"{prefix}\n*{alert_title}*\n\n{details}\n\n_Sent autonomously via Claude MCP WhatsApp Bridge_"
    return send_whatsapp_message_impl(default_phone, formatted)

def check_gateway_health_impl() -> str:
    gateway_url, api_key, _ = get_bridge_config()
    parsed = urllib.parse.urlparse(gateway_url)
    health_url = f"{parsed.scheme}://{parsed.netloc}/health"
    
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    start_t = time.time()
    req = urllib.request.Request(health_url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            elapsed_ms = int((time.time() - start_t) * 1000)
            return f"Gateway Healthy (Status {resp.status}, Latency: {elapsed_ms}ms, Endpoint: {health_url})"
    except Exception as e:
        try:
            req_base = urllib.request.Request(f"{parsed.scheme}://{parsed.netloc}/", headers=headers)
            with urllib.request.urlopen(req_base, timeout=5) as resp:
                elapsed_ms = int((time.time() - start_t) * 1000)
                return f"Gateway Reachable (Status {resp.status}, Latency: {elapsed_ms}ms)"
        except Exception as e2:
            return f"Gateway Unreachable: {gateway_url} ({e2})"

if app is not None:
    @app.tool()
    def send_whatsapp_message(phone_number: str, message: str) -> str:
        """
        Send a direct WhatsApp text message to a specific phone number.
        
        Args:
            phone_number: Destination phone number in international format (e.g. '628123456789' or '+659****4567').
            message: The plain text or formatted message to deliver.
        """
        return send_whatsapp_message_impl(phone_number, message)

    @app.tool()
    def send_whatsapp_media(phone_number: str, media_url: str, caption: Optional[str] = None, media_type: str = "image") -> str:
        """
        Send an image, document/PDF, or audio file via WhatsApp bridge.
        
        Args:
            phone_number: Destination phone number in international format.
            media_url: Publicly accessible URL or server-reachable path to the file.
            caption: Optional text caption accompanying the media.
            media_type: Type of media ('image', 'document', 'audio', 'video').
        """
        return send_whatsapp_media_impl(phone_number, media_url, caption, media_type)

    @app.tool()
    def send_whatsapp_alert(alert_title: str, details: str, urgency: str = "NORMAL") -> str:
        """
        Dispatch a formatted urgent alert to the primary administrator's WhatsApp number.
        
        Args:
            alert_title: Short title of the alert (e.g. 'Build Failed', 'Security Breach').
            details: Specific error trace or completion log.
            urgency: Priority level ('LOW', 'NORMAL', 'CRITICAL').
        """
        return send_whatsapp_alert_impl(alert_title, details, urgency)

    @app.tool()
    def check_gateway_health() -> str:
        """
        Check connectivity and latency to the configured WhatsApp bridge gateway endpoint.
        """
        return check_gateway_health_impl()

def main():
    parser = argparse.ArgumentParser(description="mcp-whatsapp-bridge CLI & MCP Server")
    parser.add_argument("--test", action="store_true", help="Test connectivity to configured WhatsApp gateway")
    parser.add_argument("--send-test", metavar="PHONE", help="Send quick test ping to specified phone number")
    args = parser.parse_args()

    if args.test:
        print("[*] Checking WhatsApp Bridge Gateway connectivity...")
        print(check_gateway_health_impl())
        sys.exit(0)

    if args.send_test:
        print(f"[*] Sending test WhatsApp message to {args.send_test}...")
        res = send_whatsapp_message_impl(args.send_test, "Test message from mcp-whatsapp-bridge CLI")
        print(res)
        sys.exit(0)

    if app is None:
        print("Error: MCP package not installed. Run with virtual environment or install mcp>=2.0.0", file=sys.stderr)
        sys.exit(1)

    app.run(transport="stdio")

if __name__ == "__main__":
    main()
