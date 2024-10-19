import base64
import logging
from abc import ABC
from email.message import EmailMessage

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from superagentx.handler.base import BaseHandler
from superagentx.handler.google.exceptions import AuthException
from superagentx.utils.helper import sync_to_async, iter_to_aiter

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
            credentials: str
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

    async def read_mail(
            self,
    ):
        try:
            events = await sync_to_async(
                self._service.users
            )
            service_messages = await sync_to_async(
                events.messages
            )
            service_lists = await sync_to_async(
                service_messages.list,
                userId='me'
            )
            result = await sync_to_async(
                service_lists.execute
            )
            messages = result.get('messages', [])

            email_data_list = []
            async for msg in iter_to_aiter(messages):
                try:
                    events = await sync_to_async(
                        self._service.users
                    )
                    service_messages = await sync_to_async(
                        events.messages
                    )
                    service_get = await sync_to_async(
                        service_messages.get,
                        userId='me',
                        id=msg.get('id')
                    )
                    txt = await sync_to_async(
                        service_get.execute
                    )
                    # Get the payload from the message
                    payload = txt.get('payload')

                    # Initialize variables for sender, receiver, and date
                    sender = None
                    receiver = None
                    date = None
                    subject = None
                    email_body = None
                    attachments = []

                    headers = payload.get('headers', [])
                    # Extract sender, receiver, and date from the headers
                    async for header in iter_to_aiter(headers):
                        if header.get('name') == 'From':
                            sender = header.get('value')
                        elif header.get('name') == 'To':
                            receiver = header.get('value')
                        elif header.get('name') == 'Date':
                            date = header.get('value')
                        elif header.get('name') == 'Subject':
                            subject = header.get('value')

                    parts = payload.get('parts', [])
                    # Extract the email body, which is usually the 'data' field in the payload
                    async for part in iter_to_aiter(parts):
                        if part.get('mimeType') == 'text/plain':  # You can also check for 'text/html'
                            data = part.get('body').get('data')
                            if data:
                                email_body = base64.urlsafe_b64decode(data).decode('utf-8')
                                break
                        if part.get('filename'):
                            attachment_id = part.get('body').get('attachmentId')
                            if attachment_id:
                                attachment = self._service.users().messages().attachments().get(
                                    userId='me', messageId=msg.get('id'), id=attachment_id
                                ).execute()
                                file_data = base64.urlsafe_b64decode(attachment.get('data'))
                                # Store the attachment information
                                attachments.append({
                                    "filename": part.get('filename'),
                                    "data": file_data
                                })
                    # Create a dictionary for the email data
                    email_data = {
                        "sender": sender,
                        "receiver": receiver,
                        "date": date,
                        "subject": subject,
                        "email_body": email_body or "No body content found.",
                        "attachments": [
                            {
                                "filename": att.get("filename")
                            }
                            for att in attachments
                        ]
                    }

                    # Add the email data dictionary to the list
                    email_data_list.append(email_data)
                except HttpError as error:
                    print(f'An error occurred: {error}')
            return email_data_list

        except Exception as ex:
            message = f"Error while Reading Mail"
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
            'read_mail'
        )
