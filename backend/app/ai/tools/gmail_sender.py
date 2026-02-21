"""Gmail sender tool — sends email via Gmail SMTP. Config: email, app password. Agent provides: to, subject, body."""

import json
import smtplib
from email.mime.text import MIMEText

from app.ai.tools.registry import register_tool
from app.ai.tools.base import SynthTool

GMAIL_SMTP_HOST = "smtp.gmail.com"
GMAIL_SMTP_PORT = 587


@register_tool("gmail_sender")
class GmailSenderTool(SynthTool):
    name: str = "gmail_sender"
    description: str = (
        "Send an email via Gmail (SMTP). Input must be a JSON object with: "
        "'to' (recipient email), 'subject' (string), 'body' (string). "
        "Optional: 'cc' (string or list), 'reply_to' (string). "
        "Credentials (email and app password) are configured on the node."
    )

    # Config from the tool node (passed as kwargs by the executor)
    email: str = ""
    password: str = ""

    def _run(self, input_str: str) -> str:
        if not self.email or not self.password:
            return "Gmail tool not configured: set email and app password on the Gmail node."
        try:
            params = json.loads(input_str)
            to = params.get("to") or params.get("recipient")
            subject = params.get("subject", "")
            body = params.get("body", "")
            if not to:
                return "Missing required field: 'to' (recipient email)."
            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"] = self.email
            msg["To"] = to if isinstance(to, str) else ", ".join(to)
            cc = params.get("cc")
            if cc:
                msg["Cc"] = cc if isinstance(cc, str) else ", ".join(cc)
            reply_to = params.get("reply_to")
            if reply_to:
                msg["Reply-To"] = reply_to
            with smtplib.SMTP(GMAIL_SMTP_HOST, GMAIL_SMTP_PORT) as s:
                s.starttls()
                s.login(self.email, self.password)
                recipients = [to] if isinstance(to, str) else list(to)
                if cc:
                    recipients.extend([cc] if isinstance(cc, str) else list(cc))
                s.sendmail(self.email, recipients, msg.as_string())
            return f"Email sent to {msg['To']}"
        except json.JSONDecodeError as e:
            return f"Invalid JSON input: {e}"
        except Exception as e:
            return f"Gmail send failed: {e}"

    async def _arun(self, input_str: str) -> str:
        return self._run(input_str)
