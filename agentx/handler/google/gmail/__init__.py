import base64
import logging
from abc import ABC
from email.message import EmailMessage

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from agentx.handler.base import BaseHandler
from agentx.handler.google.exceptions import AuthException
from agentx.utils.helper import sync_to_async

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
        self._service = self._connect()

    def _connect(self):
        """
            Establish a connection to the Gmail API.

            This private method initializes the connection to the Gmail API
            by managing the OAuth 2.0 authentication process. It verifies
            whether valid credentials are available; if not, it prompts
            the user to authenticate through a local server flow to obtain
            new credentials.

            Returns:
                googleapiclient.discovery.Resource:
                    A service object for the Gmail API, which can be used to
                    make subsequent API calls.

            Raises:
                AuthException:
                    If an error occurs during the authentication process, an
                    exception is raised with a detailed message about the
                    authentication failure.
            """

        try:
            if not self.creds or not self.creds.valid:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials, SCOPES)
                self.creds = flow.run_local_server(port=0)
            logger.info("Authenticate Success")
            return build(
                "gmail",
                "v1",
                credentials=self.creds
            )
        except Exception as ex:
            message = f'Gmail Handler Authentication Problem {ex}'
            logger.error(message, exc_info=ex)
            raise AuthException(message)

    async def get_user_profile(
            self,
            user_id: str = "me"
    ):
        """
            Retrieve the Gmail profile information for a specified user using the Gmail API.

            This asynchronous method fetches the profile details of a user from
            Gmail. If no user ID is provided, it defaults to "me", which refers
            to the authenticated user.

            Args:
                user_id (str): The ID of the user whose profile is to be
                    retrieved. Use "me" to refer to the authenticated user.
                    Defaults to "me".

            Returns:
                dict: A dictionary containing the user's profile information,
                including fields such as email address, display name, and other
                relevant details.

            """
        try:
            events = await sync_to_async(
                self._service.users
            )
            service_profile = await sync_to_async(
                events.getProfile,
                userId=user_id
            )
            return await sync_to_async(
                service_profile.execute,
            )
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
            user_id: str = "me",
            content: str = "This is automated content",
    ):
        """
            Send an email using the Gmail API.

            This asynchronous method sends an email from the specified sender
            address to the recipient.

            Args:
                from_address (str): The email address of the sender.
                to (str): The recipient's email address.
                subject (str): The subject of the email.
                user_id (str): The ID of the user sending the email.
                    Use "me" to refer to the authenticated user. Defaults to "me".
                content (str): The body content of the email. Defaults
                    to "This is automated content".

            Returns:
                dict: A dictionary containing the details of the sent email,
                including message ID.
            """
        try:
            message = EmailMessage()
            message.set_content(content)
            message["To"] = to
            message["From"] = from_address
            message["Subject"] = subject
            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            create_message = {"raw": encoded_message}
            logger.info("Message Sends Successfully")
            events = await sync_to_async(
                self._service.users
            )
            events_messages = await sync_to_async(
                events.messages
            )
            events_send = await sync_to_async(
                events_messages.send,
                userId=user_id,
                body=create_message
            )
            return await sync_to_async(
                events_send.execute,
            )
        except Exception as ex:
            message = f"Error while Send Email"
            logger.error(message, exc_info=ex)
            raise

    async def create_draft_email(
            self,
            *,
            from_address: str,
            to: str,
            subject: str = "Automated draft",
            user_id: str = "me",
            content: str = "This is automated draft mail",
    ):
        """
            Create a draft email using the Gmail API.

            This asynchronous method creates a draft email that can be edited
            or sent later. The draft is created for the specified sender and
            recipient, with optional subject and content.

            Args:
                from_address (str): The email address of the sender.
                to (str): The recipient's email address.
                subject (str): The subject of the draft email. Defaults
                    to "Automated draft".
                user_id (str): The ID of the user creating the draft.
                    Use "me" to refer to the authenticated user. Defaults to "me".
                content (str): The body content of the draft email.
                    Defaults to "This is automated draft mail".

            Returns:
                dict: A dictionary containing details of the created draft,
                including draft ID.

            """
        try:
            message = EmailMessage()
            message.set_content(content)
            message["To"] = to
            message["From"] = from_address
            message["Subject"] = subject
            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            create_message = {"message": {"raw": encoded_message}}
            logger.info("Draft message saved successfully")
            events = await sync_to_async(
                self._service.users
            )
            events_draft = await sync_to_async(
                events.drafts
            )
            events_draft_create = await sync_to_async(
                events_draft.create,
                userId=user_id,
                body=create_message
            )
            return await sync_to_async(
                events_draft_create.execute,
            )
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
