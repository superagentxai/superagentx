import os
import smtplib
from email import encoders
from email.message import EmailMessage
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from enum import Enum
from ssl import SSLContext
from typing import Any

from agentx.handler.base import BaseHandler
from agentx.handler.email.exceptions import SendEmailFailed, InvalidEmailAction


class EmailAction(str, Enum):
    SEND = "SEND"
    READ = "READ"


class EmailHandler(BaseHandler):

    def __init__(
            self,
            host: str,
            port: int,
            username: str | None = None,
            password: str | None = None,
            ssl: bool = False,
            ssl_context: SSLContext | None = None
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.ssl = ssl
        if ssl:
            self._conn = smtplib.SMTP_SSL(
                host=host,
                port=port,
                context=ssl_context
            )
        else:
            self._conn = smtplib.SMTP(
                host=host,
                port=port
            )

    def handle(
            self,
            *,
            action: str | Enum,
            **kwargs
    ) -> Any:
        match action:
            case EmailAction.SEND:
                return self.send_email(**kwargs)
            case EmailAction.READ:
                raise NotImplementedError
            case _:
                raise InvalidEmailAction(f"Invalid email action `{action}`")

    def send_email(
            self,
            *,
            sender: str,
            to: list[str],
            subject: str,
            body: str,
            from_name: str | None = None,
            cc: list[str] | None = None,
            bcc: list[str] | None = None,
            attachment_path: str | None = None
    ):
        try:
            msg = EmailMessage()
            msg['From'] = f"{from_name} <{sender}>"
            msg['To'] = ', '.join(to)
            msg['Cc'] = ', '.join(cc) if cc else ''
            msg['Bcc'] = ', '.join(bcc) if bcc else ''
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'plain'))

            if attachment_path:
                attachment_name = os.path.basename(attachment_path)
                with open(attachment_path, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f"attachment; filename= {attachment_name}")
                    msg.attach(part)

            all_recipients = to + (cc or []) + (bcc or [])

            if self.username and self.password:
                self._conn.login(user=self.username, password=self.password)

            res = self._conn.sendmail(
                from_addr=sender,
                to_addrs=all_recipients,
                msg=msg.as_string()
            )
            self._conn.close()
            return res
        except Exception as e:
            raise SendEmailFailed(f"Failed to send email!\n{e}")
