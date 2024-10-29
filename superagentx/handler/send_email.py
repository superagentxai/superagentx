import logging
import os
import smtplib
from email import encoders
from email.message import EmailMessage
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from ssl import SSLContext

from superagentx.handler.base import BaseHandler
from superagentx.handler.decorators import tool
from superagentx.utils.helper import sync_to_async

logger = logging.getLogger(__name__)


class SendEmailFailed(Exception):
    pass


class EmailHandler(BaseHandler):
    """
     A handler class for managing email operations.
    This class extends BaseHandler and provides methods for sending emails, managing recipients,
    and handling attachments, facilitating efficient email communication.

    """

    def __init__(
            self,
            host: str,
            port: int,
            username: str | None = None,
            password: str | None = None,
            ssl: bool = False,
            ssl_context: SSLContext | None = None
    ):
        super().__init__()
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

    @tool
    async def send_email(
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

        """
        Asynchronously sends an email with specified parameters, including sender, recipients, subject, and body.
        This method also supports optional fields such as CC, BCC, and attachments for comprehensive email communication.

        parameter:
            sender (str): The email address of the sender.
            to (list[str]): A list of recipient email addresses to whom the email will be sent.
            subject (str): The subject line of the email.
            body (str): The content of the email.
            from_name (str | None, optional): The name of the sender to display in the email. Defaults to None.
            cc (list[str] | None, optional): A list of email addresses to be included in the CC field. Defaults to None.
            bcc (list[str] | None, optional): A list of email addresses to be included in the BCC field. Defaults to None.
            attachment_path (str | None, optional): The file path of any attachment to be included with the email. Defaults to None.
        """

        try:
            msg = EmailMessage() if not attachment_path else MIMEMultipart()
            msg.set_content(body)
            msg['From'] = f"{from_name} <{sender}>"
            msg['To'] = ', '.join(to)
            msg['Cc'] = ', '.join(cc) if cc else ''
            msg['Bcc'] = ', '.join(bcc) if bcc else ''
            msg['Subject'] = subject

            if attachment_path:
                attachment_name = os.path.basename(attachment_path)
                async with open(attachment_path, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    await sync_to_async(part.set_payload, await attachment.read())
                    await sync_to_async(encoders.encode_base64, part)
                    await sync_to_async(
                        part.add_header,
                        'Content-Disposition',
                        f"attachment; filename= {attachment_name}"
                    )
                    await sync_to_async(
                        msg.attach,
                        part
                    )

            all_recipients = to + (cc or []) + (bcc or [])

            if self.username and self.password:
                await sync_to_async(
                    self._conn.login,
                    user=self.username,
                    password=self.password
                )

            res = await sync_to_async(
                self._conn.sendmail,
                from_addr=sender,
                to_addrs=all_recipients,
                msg=msg.as_string()
            )
            await sync_to_async(self._conn.close)
            return res
        except Exception as e:
            logger.error('Failed to send email!', exc_info=e)
            raise SendEmailFailed(f"Failed to send email!\n{e}")
