#!/usr/bin/env python3
"""
mcp-whatsapp-bridge — Model Context Protocol (MCP) Server for WhatsApp Automation.
Enables Claude Desktop, Claude Code, and autonomous AI agents to dispatch direct WhatsApp messages,
alerts, and status reports to personal or team WhatsApp numbers without expensive third-party Twilio APIs.
Supports both local gateway bridges and direct HTTP webhook routing.
"""

import os
import sys
import json
import urllib.request
import urllib.error
import argparse
from typing import Optional
from mcp.server.mcpserver import MCPServer

app = MCPServer("whatsapp-bridge-mcp")

def get_bridge_config():
    gateway_url = os.environ.get("WHATSAPP_GATEWAY_URL", "http://localhost:3001/send")
    api_key = os.environ.get("WHATSAPP_API_KEY", "")
    default_recipient = os.environ.get("WHATSAPP_DEFAULT_PHONE", "")
    return gateway_url, api_key, default_recipient

@app.tool()
def send_whatsapp_message(phone_number: str, message: str) -> str:
    """
    Send a direct WhatsApp text message to a specific phone number.
    
    Args:
        phone_number: Destination phone number in international format (e.g. '628123456789' or '+6591234567').
        message: The plain text or formatted message to deliver.
    """
    gateway_url, api_key, default_phone = get_bridge_config()
    target_phone = phone_number or default_phone
    if not target_phone:
        return "Error: No destination phone number provided and WHATSAPP_DEFAULT_PHONE is not set."

    # Format numbers: strip spaces, dashes, plus signs
    cleaned_phone = target_phone.replace("+", "").replace("-", "").replace(" ", "").strip()
    
    payload = {
        "to": cleaned_phone,
        "message": message
    }
    
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
        
    req = urllib.request.Request(gateway_url, data=json.dumps(payload).encode("utf-8"), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return f"Successfully delivered WhatsApp message to {cleaned_phone} (Status: {data.get('status', 'sent')})."
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8")
        return f"HTTP Error sending WhatsApp ({e.code}): {err}"
    except Exception as e:
        return f"Failed to send WhatsApp message via bridge ({gateway_url}): {e}"

@app.tool()
def send_whatsapp_alert(alert_title: str, details: str, urgency: str = "NORMAL") -> str:
    """
    Dispatch a formatted urgent alert to the primary administrator's WhatsApp number.
    
    Args:
        alert_title: Short title of the alert (e.g. 'Build Failed', 'Security Breach').
        details: Specific error trace or completion log.
        urgency: Priority level ('LOW', 'NORMAL', 'CRITICAL').
    """
    _, _, default_phone = get_bridge_config()
    if not default_phone:
        return "Error: WHATSAPP_DEFAULT_PHONE is not configured in the environment."
        
    prefix = "🚨 *[CRITICAL ALERT]*" if urgency.upper() == "CRITICAL" else "📢 *[AGENT NOTIFICATION]*"
    formatted = f"{prefix}\n*{alert_title}*\n\n{details}\n\n_Sent autonomously via Claude MCP WhatsApp Bridge_"
    return send_whatsapp_message(default_phone, formatted)

if __name__ == "__main__":
    app.run(transport="stdio")
