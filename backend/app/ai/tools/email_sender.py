import json
from app.ai.tools.registry import register_tool
from app.ai.tools.base import SynthTool


@register_tool("email_sender")
class EmailSenderTool(SynthTool):
    name: str = "email_sender"
    description: str = "Send an email via SMTP. Input: JSON with 'to', 'subject', 'body', 'smtp_host', 'smtp_port', 'username', 'password'."

    def _run(self, input_str: str) -> str:
        import smtplib
        from email.mime.text import MIMEText
        try:
            params = json.loads(input_str)
            msg = MIMEText(params["body"])
            msg["Subject"] = params["subject"]
            msg["From"] = params["username"]
            msg["To"] = params["to"]
            with smtplib.SMTP(params.get("smtp_host", "smtp.gmail.com"), int(params.get("smtp_port", 587))) as s:
                s.starttls()
                s.login(params["username"], params["password"])
                s.send_message(msg)
            return f"Email sent to {params['to']}"
        except Exception as e:
            return f"Email failed: {e}"

    async def _arun(self, input_str: str) -> str:
        return self._run(input_str)
