import base64
import logging
from abc import ABC
from email.message import EmailMessage
from agentx.handler.base import BaseHandler
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from agentx.handler.google.exceptions import AuthException

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://mail.google.com/",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.compose"
]


class GmailHandler(BaseHandler, ABC):
    def __init__(
            self,
            *,
            credentials: dict
    ):
        self.creds = None
        logger.info(f'Gmail client initialization')
        self.credentials = credentials or {}
        self.service = self._connect()

    def _connect(self):
        try:
            if not self.creds or not self.creds.valid:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials, SCOPES)
                self.creds = flow.run_local_server(port=0)
            service = build("gmail", "v1", credentials=self.creds)
            logger.info("Authenticate Success")
            return service
        except Exception as ex:
            message = f'Gmail Handler Authentication Problem {ex}'
            logger.error(message, exc_info=ex)
            raise AuthException(message)

    async def get_user_profile(
            self,
            user_id: str | None = "me"
    ):
        try:
            result = await self.service.users().getProfile(userId=user_id).execute()
            logger.info(f"Email Address=>> {result["emailAddress"]}")
            logger.info(f"Inbox Total Messages=>> {result["threadsTotal"]}")
            return result
        except Exception as ex:
            message = f"Error while Getting Profile"
            logger.error(message, exc_info=ex)
            raise

    async def send_email(
            self,
            *,
            from_address: str,
            to: str,
            subject: str,
            user_id: str | None = "me",
            content: str | None = "This is automated content",
    ):
        try:
            message = EmailMessage()
            message.set_content(content)
            message["To"] = to
            message["From"] = from_address
            message["Subject"] = subject
            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            create_message = {"raw": encoded_message}
            result = await self.service.users().messages().send(userId=user_id, body=create_message).execute()
            logger.info(f"Message Sends Successfully =>> {result["id"]}")
        except Exception as ex:
            message = f"Error while Send Email"
            logger.error(message, exc_info=ex)
            raise

    async def create_draft_email(
            self,
            *,
            from_address: str,
            to: str,
            subject: str | None = "Automated draft",
            user_id: str | None = "me",
            content: str | None = "This is automated draft mail",
    ):
        try:
            message = EmailMessage()
            message.set_content(content)
            message["To"] = to
            message["From"] = from_address
            message["Subject"] = subject
            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            create_message = {"message": {"raw": encoded_message}}
            result = await self.service.users().drafts().create(userId=user_id, body=create_message).execute()
            logger.info(f"Draft message saved successfully {result["id"]}")
        except Exception as ex:
            message = f"Error while Create Draft Email"
            logger.error(message, exc_info=ex)
            raise

    def __dir__(self):
        return (
            'get_user_profile',
            'send_email',
            'create_draft_email',
        )
