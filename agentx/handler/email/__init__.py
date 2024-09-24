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
from agentx.utils.helper import sync_to_async


class EmailAction(str, Enum):
    SEND = "send"
    READ = "read"


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

    async def handle(
            self,
            *,
            action: str | Enum,
            **kwargs
    ) -> Any:

        """
        Asynchronously processes the specified action, which can be a string or an Enum, along with any additional
        keyword arguments. This method executes the corresponding logic based on the provided action and parameters.

        parameters:
            action (str | Enum): The action to be performed. This can either be a string or an Enum value representing
                                the action.
            **kwargs: Additional keyword arguments that may be passed to customize the behavior of the handler.

        Returns:
            Any: The result of handling the action. The return type may vary depending on the specific action handled.
        """

        if isinstance(action, str):
            action = action.lower()
        match action:
            case EmailAction.SEND:
                return await self.send_email(**kwargs)
            case EmailAction.READ:
                raise NotImplementedError
            case _:
                raise InvalidEmailAction(f"Invalid email action `{action}`")

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
            msg = EmailMessage()
            msg['From'] = f"{from_name} <{sender}>"
            msg['To'] = ', '.join(to)
            msg['Cc'] = ', '.join(cc) if cc else ''
            msg['Bcc'] = ', '.join(bcc) if bcc else ''
            msg['Subject'] = subject

            await sync_to_async(msg.attach,MIMEText(body, 'plain'))

            if attachment_path:
                attachment_name = os.path.basename(attachment_path)
                async with open(attachment_path, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    await sync_to_async(part.set_payload,await attachment.read())
                    await sync_to_async(encoders.encode_base64,part)
                    await sync_to_async(
                        part.add_header,
                        'Content-Disposition',
                        f"attachment; filename= {attachment_name}"
                    )
                    await sync_to_async(msg.attach,part)

            all_recipients = to + (cc or []) + (bcc or [])

            if self.username and self.password:
                await sync_to_async(self._conn.login,user=self.username, password=self.password)

            res = await sync_to_async(self._conn.sendmail,
                from_addr=sender,
                to_addrs=all_recipients,
                msg=await sync_to_async(msg.as_string)
            )
            await sync_to_async(self._conn.close)
            return res
        except Exception as e:
            raise SendEmailFailed(f"Failed to send email!\n{e}")

    def __dir__(self):
        return (
            "send_email"
        )
