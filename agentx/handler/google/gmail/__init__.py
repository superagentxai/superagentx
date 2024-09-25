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
        """
            Retrieve the Gmail profile information for a specified user using the Gmail API.

            This asynchronous method fetches the profile details of a user from
            Gmail. If no user ID is provided, it defaults to "me", which refers
            to the authenticated user.

            Args:
                user_id (str | None): The ID of the user whose profile is to be
                    retrieved. Use "me" to refer to the authenticated user.
                    Defaults to "me".

            Returns:
                dict: A dictionary containing the user's profile information,
                including fields such as email address, display name, and other
                relevant details.

            """
        try:
            result = self.service.users().getProfile(userId=user_id).execute()
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
        """
            Send an email using the Gmail API.

            This asynchronous method sends an email from the specified sender
            address to the recipient.

            Args:
                from_address (str): The email address of the sender.
                to (str): The recipient's email address.
                subject (str): The subject of the email.
                user_id (str | None): The ID of the user sending the email.
                    Use "me" to refer to the authenticated user. Defaults to "me".
                content (str | None): The body content of the email. Defaults
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
            result = self.service.users().messages().send(userId=user_id, body=create_message).execute()
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
        """
            Create a draft email using the Gmail API.

            This asynchronous method creates a draft email that can be edited
            or sent later. The draft is created for the specified sender and
            recipient, with optional subject and content.

            Args:
                from_address (str): The email address of the sender.
                to (str): The recipient's email address.
                subject (str | None): The subject of the draft email. Defaults
                    to "Automated draft".
                user_id (str | None): The ID of the user creating the draft.
                    Use "me" to refer to the authenticated user. Defaults to "me".
                content (str | None): The body content of the draft email.
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
            result = self.service.users().drafts().create(userId=user_id, body=create_message).execute()
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
