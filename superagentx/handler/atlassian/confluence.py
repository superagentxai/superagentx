import logging
import os

import aiohttp
from aiohttp import BasicAuth
from atlassian import Confluence

from superagentx.handler.base import BaseHandler
from superagentx.handler.atlassian.exceptions import AuthException
from superagentx.utils.helper import sync_to_async

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
            email: str | None = None,
            token: str | None = None,
            organization: str | None = None
    ):
        self.email = email or os.getenv('ATLASSIAN_EMAIL')
        self.token = token or os.getenv('ATLASSIAN_TOKEN')
        self.organization = organization or os.getenv('ATLASSIAN_ORGANIZATION')
        self._connection: Confluence = self._connect()

    def _connect(self) -> Confluence:
        try:
            confluence = Confluence(
                url=f'https://{self.organization}.atlassian.net',
                token=self.token
            )
            logger.info("Confluence Authenticate Success")
            return confluence
        except Exception as ex:
            message = f'Confluence Handler Authentication Problem {ex}'
            logger.error(message, exc_info=ex)
            raise AuthException(message)

    async def get_all_spaces(
            self,
            *,
            start: int = 0,
            limit: int = 25,
    ):
        try:
            result = await sync_to_async(
                self._connection.get_all_spaces,
                start=start,
                limit=limit,
            )
            spaces_url = result["_links"]["self"]
            async with aiohttp.ClientSession() as session:
                async with session.get(
                        spaces_url,
                        auth=BasicAuth(self.email, self.token),
                        headers={'Content-Type': 'application/json'}
                ) as resp:
                    return await resp.json()
        except Exception as ex:
            message = f"Error While getting confluence spaces! {ex}"
            logger.error(message, exc_info={ex})
            raise Exception(message)

    async def get_pages_spaces(
            self,
            *,
            space_key: str,
            start: int = 0,
            limit: int = 25,
    ):
        try:
            result = await sync_to_async(
                self._connection.get_all_pages_from_space,
                space=space_key,
                expand="children.page",
                start=start,
                limit=limit
            )
            return result
        except Exception as ex:
            message = f"Error While getting confluence spaces! {ex}"
            logger.error(message, exc_info={ex})
            raise Exception(message)

    async def download_pages(self):
        try:
            result = await sync_to_async(
                self._connection.export_page,
                page_id=959938561
            )
            return result
        except Exception as ex:
            message = f"Error While getting confluence spaces! {ex}"
            logger.error(message, exc_info={ex})
            raise Exception(message)

    def __dir__(self):
        return (
            'get_all_spaces',
            'get_pages_spaces',
            'download_pages'
        )
