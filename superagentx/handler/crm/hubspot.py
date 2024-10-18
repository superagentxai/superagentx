import logging

from hubspot import HubSpot
from hubspot.crm.contacts import SimplePublicObjectInputForCreate, ApiException, PublicObjectSearchRequest

from superagentx.handler.base import BaseHandler
from superagentx.handler.atlassian.exceptions import AuthException
from superagentx.utils.helper import sync_to_async

logger = logging.getLogger(__name__)


class HubSpotHandler(BaseHandler):
    """
        A handler class for managing interactions with the Hubspot API.
        This class extends BaseHandler and provides methods for performing various operations,
        such as creating, updating, retrieving, and managing within a Hubspot environment.
    """
    def __init__(
            self,
            *,
            token: str
    ):
        self.token = token
        self._connection: HubSpot = self._connect()

    def _connect(self) -> HubSpot:
        """
            Establish a connection to the HubSpot API.

            This method initializes and returns an instance of the HubSpot client,
            allowing for subsequent interactions with the HubSpot API. It handles
            any necessary authentication and setup required for the connection.

            Returns:
                HubSpot: An instance of the HubSpot client connected to the API.
            """
        try:
            api_client = HubSpot(
                access_token=self.token
            )
            logger.debug("Authenticate Success")
            return api_client
        except Exception as ex:
            message = f'HubSpot Handler Authentication Problem {ex}'
            logger.error(message, exc_info=ex)
            raise AuthException(message)

    async def create_contact(
            self,
            email: str,
            firstName: str = '',
            lastName: str = ''
    ):
        """
            create a new contact in HubSpot.

            This method sends a request to the HubSpot API to create a new contact
            using the provided email address, first name, and last name.

            Args:
                email (str): The email address of the contact. This field is required.
                firstName (str, optional): The first name of the contact. Defaults to an empty string.
                lastName (str, optional): The last name of the contact. Defaults to an empty string.

            Returns:
                dict: A dictionary containing the details of the created contact info.

            """
        try:
            simple_public_object_input_for_create = SimplePublicObjectInputForCreate(
                properties={
                    "email": email,
                    "firstname": firstName,
                    "lastname": lastName
                }
            )
            return await sync_to_async(
                self._connection.crm.contacts.basic_api.create,
                simple_public_object_input_for_create=simple_public_object_input_for_create
            )
        except ApiException as ex:
            message = f"Exception when creating contact {ex}"
            logger.error(message, exc_info=ex)
            raise

    async def get_all_contact(
            self
    ):
        """
            retrieve all contacts from HubSpot.

            This method sends a request to the HubSpot API to fetch a list of all contacts
            associated with the account.

            Returns:
                list: A list of dictionaries, each containing details of a contact, such as
                      email, first name, last name etc..

            """
        try:
            return await sync_to_async(
                self._connection.crm.contacts.get_all
            )
        except ApiException as ex:
            message = f"Exception when getting contacts {ex}"
            logger.error(message, exc_info=ex)
            raise

    async def create_company(
            self,
            *,
            name: str,
            domain: str = ""
    ):
        """
            create a new company in HubSpot.

            This method sends a request to the HubSpot API to create a new company
            using the provided name and an optional domain.

            Args:
                name (str): The name of the company. This field is required.
                domain (str, optional): The domain of the company. Defaults to an empty string.

            Returns:
                dict: A dictionary containing the details of the created company info
            """
        try:
            simple_public_object_input_for_create = SimplePublicObjectInputForCreate(
                properties={
                    "domain": domain,
                    "name": name
                }
            )
            return await sync_to_async(
                self._connection.crm.companies.basic_api.create,
                simple_public_object_input_for_create=simple_public_object_input_for_create
            )
        except ApiException as ex:
            message = f"Exception when creating Company {ex}"
            logger.error(message, exc_info=ex)
            raise

    async def get_all_company(
            self
    ):
        """
            retrieve all companies from HubSpot.

            This method sends a request to the HubSpot API to fetch a list of all companies
            associated with the account.

            Returns:
                list: A list of dictionaries, each containing details of a company, such as
                      name, domain, etc...
            """
        try:
            return await sync_to_async(
                self._connection.crm.companies.get_all
            )
        except ApiException as ex:
            message = f"Exception when getting company {ex}"
            logger.error(message, exc_info=ex)
            raise

    async def get_all_deals(
            self
    ):
        """
            Get the all Deals from HubSpot.

            This method sends a request to the HubSpot API to fetch a list of all deals
            associated with the account.

            Returns:
                list: A list of dictionaries, each containing details of a deal, such as
                      deal name, amount, stage, etc...
            """
        try:
            return await sync_to_async(
                self._connection.crm.deals.get_all
            )
        except ApiException as ex:
            message = f"Exception when getting deals {ex}"
            logger.error(message, exc_info=ex)
            raise

    async def get_all_tickets(
            self
    ):
        """
            retrieve all tickets from HubSpot.

            This method sends a request to the HubSpot API to fetch a list of all tickets
            associated with the account.

            Returns:
                list: A list of dictionaries, each containing details of a ticket, such as
                      ticket ID, status, subject, and associated contact.

            """
        try:
            return await sync_to_async(
                self._connection.crm.tickets.get_all
            )
        except ApiException as ex:
            message = f"Exception when getting tickets {ex}"
            logger.error(message, exc_info=ex)
            raise

    def __dir__(self):
        return (
            'create_contact',
            'get_all_contact',
            'create_company',
            'get_all_company',
            'get_all_deals',
            'get_all_tickets'
        )
