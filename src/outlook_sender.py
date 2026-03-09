from __future__ import annotations

from pathlib import Path
from typing import Any, Dict


class OutlookSender:
    def __init__(self, config: Dict[str, Any], logger):
        self.config = config
        self.logger = logger

    def send_html_report(self, subject: str, html_body: str) -> None:
        try:
            import win32com.client  # type: ignore
        except ImportError as exc:
            raise RuntimeError("pywin32 is required on Windows for Outlook sending") from exc

        outlook = win32com.client.Dispatch("Outlook.Application")
        mail = outlook.CreateItem(0)
        mail.Subject = subject
        mail.HTMLBody = html_body
        mail.To = ";".join(self.config["outlook"].get("to", []))
        mail.CC = ";".join(self.config["outlook"].get("cc", []))
        mail.Importance = self.config["outlook"].get("importance", 2)

        mode = self.config["app"].get("send_mode", "draft").lower()
        if mode == "send":
            mail.Send()
            self.logger.info("Outlook mail sent: %s", subject)
        else:
            mail.Save()
            mail.Display(False)
            self.logger.info("Outlook draft created: %s", subject)
