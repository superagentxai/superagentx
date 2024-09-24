from enum import Enum
from typing import Any

import wikipedia

from agentx.handler.base import BaseHandler
from agentx.handler.wikipedia.exceptions import InvalidAction
from agentx.utils.helper import sync_to_async


class SearchAction(str, Enum):
    SUMMARY = "summary"
    SEARCH = "search"


class WikipediaHandler(BaseHandler):
    """
        A handler class for managing interactions with the Wikipedia API.
        This class extends BaseHandler and provides methods for retrieving and processing content
        from Wikipedia, including searching articles, fetching summaries, and accessing structured data.
    """

    async def handle(
            self,
            action: str | Enum,
            *args,
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
            case SearchAction.SUMMARY:
                return await self.get_summary(**kwargs)
            case SearchAction.SEARCH:
                return await self.get_search(**kwargs)
            case _:
                raise InvalidAction(f'Invalid Action `{action}`')

    @staticmethod
    async def get_summary(
            query: str | None = None,
            sentences: int | None = None,
            language: str | None = None
    ):

        """
        Asynchronously retrieves a summary of a specified topic or content.
        This method condenses information into a concise format, making it easier to understand key points at a glance.

        parameter:
            query (str | None, optional): The search query to retrieve relevant information. Defaults to None.
            sentences (int | None, optional): The maximum number of sentences to return in the response. Defaults to None.
            language (str | None, optional): The language code for the response content. Defaults to None.

        """


        if language:
            await sync_to_async(wikipedia.set_lang,language)

        result = await sync_to_async(wikipedia.summary,query, sentences=sentences)
        return result

    @staticmethod
    async def get_search(
            query: str | None = None,
            results: int | None = None,
            language: str | None = None
    ):

        """
        Asynchronously performs a search operation based on the specified parameters.
        This method retrieves relevant results based on the query and other filters, such as language and result limits.

        parameter:
            query (str | None, optional): The search query to retrieve relevant information. Defaults to None.
            results (int | None, optional): The maximum number of results to return. Defaults to None, indicating
            no limit on the number of results.
            language (str | None, optional): The language code for the response content. Defaults to None.

        """

        if language:
            await sync_to_async(wikipedia.set_lang,language)

        results = await sync_to_async(wikipedia.search, query, results=results)
        return results

    def __dir__(self):
        return(
            'get_summary',
            'get_search'
        )
