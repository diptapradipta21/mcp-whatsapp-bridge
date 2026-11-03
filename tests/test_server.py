#!/usr/bin/env python3
import unittest
from unittest.mock import patch, MagicMock
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from server import (
    clean_phone_number,
    send_whatsapp_message_impl,
    send_whatsapp_media_impl,
    send_whatsapp_alert_impl,
    check_gateway_health_impl
)

class TestWhatsAppBridge(unittest.TestCase):
    def test_clean_phone_number(self):
        self.assertEqual(clean_phone_number("+62 812-3456-7890"), "6281234567890")
        self.assertEqual(clean_phone_number("(+65) 9100 1610"), "6591001610")

    @patch("urllib.request.urlopen")
    def test_send_message_success(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"status": "delivered"}).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        res = send_whatsapp_message_impl("628123456789", "Hello World")
        self.assertIn("Successfully delivered", res)
        self.assertIn("628123456789", res)

    @patch("urllib.request.urlopen")
    def test_send_media_success(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"status": "queued"}).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        res = send_whatsapp_media_impl("628123456789", "https://example.com/report.pdf", "Monthly Report", "document")
        self.assertIn("Successfully delivered document", res)

    @patch("urllib.request.urlopen")
    def test_send_alert(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"status": "sent"}).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        with patch.dict("os.environ", {"WHATSAPP_DEFAULT_PHONE": "6289999999"}):
            res = send_whatsapp_alert_impl("DB Down", "Connection refused on port 5432", urgency="CRITICAL")
            self.assertIn("Successfully delivered", res)

    @patch("urllib.request.urlopen")
    def test_gateway_health(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        res = check_gateway_health_impl()
        self.assertIn("Gateway Healthy", res)

if __name__ == "__main__":
    unittest.main()
