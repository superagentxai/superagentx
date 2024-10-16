import logging

from atlassian import Confluence

from agentx.handler.base import BaseHandler
from agentx.handler.atlassian.exceptions import AuthException
from agentx.utils.helper import sync_to_async, iter_to_aiter


logger = logging.getLogger(__name__)


class ConfluenceHandler(BaseHandler):
    """
        A handler class for managing interactions with the Jira API.
        This class extends BaseHandler and provides methods for performing various Jira operations,
        such as creating, updating, retrieving, and managing issues and projects within a Jira environment.
    """

    def __init__(
            self,
            *,
            token: str,
            organization: str
    ):
        self.token = token
        self.organization = organization
        self._connection: Confluence = self._connect()

    def _connect(self) -> Confluence:
        try:
            confluence = Confluence(
                url=f'https://{self.organization}.atlassian.net',
                token=self.token
            )
            logger.debug("Authenticate Success")
            return confluence
        except Exception as ex:
            message = f'Confluence Handler Authentication Problem {ex}'
            logger.error(message, exc_info=ex)
            raise AuthException(message)

    async def get_all_groups(
            self,
            *,
            start: int = 0,
            limit: int = 10,
    ):
        try:
            return await sync_to_async(
                self._connection.get_all_groups,
                start=start,
                limit=limit
            )
        except Exception as ex:
            message = f"Error While getting confluence Groups! {ex}"
            logger.error(message, exc_info={ex})
            raise Exception(message)

    def __dir__(self):
        return (
            'get_all_groups'
        )
