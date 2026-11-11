# 💬 WhatsApp Bridge MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![MCP Standard](https://img.shields.io/badge/MCP-2.0-orange.svg)](https://modelcontextprotocol.io/)
[![Claude Ready](https://img.shields.io/badge/Claude-Desktop%20%26%20Code-purple.svg)](https://claude.ai/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

> **Official Model Context Protocol (MCP 2.0) server enabling Claude Desktop, Claude Code, and autonomous AI agents to dispatch direct WhatsApp messages, documents, media, urgent build alerts, and report summaries to personal or team phones.**

---

## 💡 The Problem
AI agents can manipulate files, browse the web, and run terminal commands, but they lack a seamless way to ping developers on **WhatsApp** when a 3-hour build finishes, a production error fires, or human approval is needed. Traditional solutions rely on expensive third-party enterprise providers (Twilio / MessageBird) with heavy monthly fees.

## 🚀 The Solution
`mcp-whatsapp-bridge` gives Claude native tools to route text, rich alerts, and documents directly through any local WhatsApp session (Baileys / Puppeteer / self-hosted gateway) or direct webhook endpoints.

---

## 🛠️ Available MCP Tools

| Tool | Parameters | Description |
| :--- | :--- | :--- |
| `send_whatsapp_message` | `phone_number`, `message` | Sends a direct message to any international phone number. |
| `send_whatsapp_media` | `phone_number`, `media_url`, `caption`, `media_type` | Dispatches an image, PDF document, or audio file with optional caption. |
| `send_whatsapp_alert` | `alert_title`, `details`, `urgency` | Sends an emergency formatted notification to the admin phone. |
| `check_gateway_health` | *(None)* | Probes gateway health endpoint and reports latency in milliseconds. |

---

## 📦 Setup & Configuration

### Environment Variables
| Variable | Description | Default |
|---|---|---|
| `WHATSAPP_GATEWAY_URL` | URL of the WhatsApp bridge gateway | `http://localhost:3001/send` |
| `WHATSAPP_DEFAULT_PHONE` | Default administrator phone for alerts | *(Optional)* |
| `WHATSAPP_API_KEY` | Bearer authorization token | *(Optional)* |

### 1. Claude Desktop Integration
Add the server to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "whatsapp-bridge": {
      "command": "python3",
      "args": ["/path/to/mcp-whatsapp-bridge/server.py"],
      "env": {
        "WHATSAPP_GATEWAY_URL": "http://localhost:3001/send",
        "WHATSAPP_DEFAULT_PHONE": "+6281234567890",
        "WHATSAPP_API_KEY": "optional_bearer_token"
      }
    }
  }
}
```

### 2. Claude Code CLI Integration
```bash
claude mcp add whatsapp-bridge -- python3 /path/to/server.py
```

### 3. CLI Diagnostics Mode
Test connection to your gateway without launching the full MCP loop:

```bash
python3 server.py --test
python3 server.py --test --json
```

---

## 🧪 Running Tests

```bash
python3 tests/test_server.py
```

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
