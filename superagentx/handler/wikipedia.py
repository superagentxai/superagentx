import logging
import re

from wikipediaapi import Wikipedia, WikipediaPage

from superagentx.handler.base import BaseHandler

logger = logging.getLogger(__name__)


class InvalidAction(Exception):
    pass


class WikipediaHandler(BaseHandler):
    """
        A handler class for managing interactions with the Wikipedia API.
        This class extends BaseHandler and provides methods for retrieving and processing content
        from Wikipedia, including searching articles, fetching summaries, and accessing structured data.
    """

    def __init__(self, lang: str = 'en'):
        self.wiki_client = Wikipedia('superagentx-wiki', lang)

    async def _get_wikipedia_page(self, query: str) -> WikipediaPage | None:
        return self.wiki_client.page(query) if query else None

    async def get_summary(self,
                          query: str
                          ) -> str:
        """
        Asynchronously retrieves a summary of a specified topic or content.
        This method condenses information into a concise format, making it easier to understand key points at a glance.

        parameter:
            query (str | None, optional): The search query to retrieve relevant information. Defaults to None.
        """
        page = await self._get_wikipedia_page(query=query)
        summary = re.escape(page.summary)
        logger.debug(f"Page Summary => {page.summary}")
        return summary if page else None

    def __dir__(self):
        return (
            'get_summary',
        )
