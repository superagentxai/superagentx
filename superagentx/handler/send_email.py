import logging
import os
import smtplib
from email.message import EmailMessage
from ssl import SSLContext
from typing import Optional, List

from superagentx.handler.base import BaseHandler
from superagentx.handler.decorators import tool
from superagentx.utils.helper import sync_to_async

logger = logging.getLogger(__name__)


class SendEmailFailed(Exception):
    pass


class EmailHandler(BaseHandler):
    """
    Handler class for managing email operations.
    """

    def __init__(
            self,
            host: str,
            port: int,
            username: Optional[str] = None,
            password: Optional[str] = None,
            ssl: bool = False,
            ssl_context: Optional[SSLContext] = None
    ):
        super().__init__()
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.ssl = ssl
        self.ssl_context = ssl_context

        # ⚠ Do NOT create the SMTP connection here.
        # It must be created per-email, inside send_email.
        self._conn = None

    @tool
    async def send_email(
            self,
            *,
            sender: str,
            to: list[str],
            subject: str,
            body: str,
            from_name: Optional[str] = None,
            cc: Optional[List[str]] = None,
            bcc: Optional[List[str]] = None,
            attachment_path: Optional[str] = None,
    ):
        try:
            # 1. Build Email

            msg = EmailMessage()
            msg.set_content(body)

            msg["From"] = f"{from_name} <{sender}>" if from_name else sender
            msg["To"] = ", ".join(to)

            if cc:
                msg["Cc"] = ", ".join(cc)
            if bcc:
                msg["Bcc"] = ", ".join(bcc)

            msg["Subject"] = subject.strip()
            all_recipients = to + (cc or []) + (bcc or [])

            # Attach file
            if attachment_path:
                filename = os.path.basename(attachment_path)
                with open(attachment_path, "rb") as f:
                    file_data = f.read()

                msg.add_attachment(
                    file_data,
                    maintype="application",
                    subtype="octet-stream",
                    filename=filename
                )

            # 2. Create and connect SMTP

            def create_conn():
                if self.ssl:
                    return smtplib.SMTP_SSL(
                        host=self.host,
                        port=self.port,
                        context=self.ssl_context
                    )
                else:
                    return smtplib.SMTP(
                        host=self.host,
                        port=self.port
                    )

            self._conn = await sync_to_async(create_conn)

            # Explicit connect (fixes your error)

            await sync_to_async(self._conn.connect, self.host, self.port)

            # 3. TLS

            if not self.ssl:
                try:
                    await sync_to_async(self._conn.starttls)
                except Exception:
                    # Some SMTP debug servers don't support TLS
                    pass

            # 4. Login

            if self.username and self.password:
                await sync_to_async(
                    self._conn.login,
                    self.username,
                    self.password
                )

            # 5. Send the email

            res = await sync_to_async(
                self._conn.sendmail,
                sender,
                all_recipients,
                msg.as_string()
            )

            return res

        except Exception as e:
            logger.error("Failed to send email!", exc_info=e)
            raise SendEmailFailed(f"Failed to send email!\n{e}")

        finally:
            # 6. Quit connection safely

            if self._conn:
                try:
                    await sync_to_async(self._conn.quit)
                except Exception:
                    pass
