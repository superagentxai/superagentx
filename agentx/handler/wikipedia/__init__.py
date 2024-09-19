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

    def handle(
            self,
            action: str | Enum,
            *args,
            **kwargs
    ) -> Any:

        """
            params:
                action(str): Give an action what has given in the Enum.
        """

        if isinstance(action, str):
            action = action.lower()
        match action:
            case SearchAction.SUMMARY:
                return self.get_summary(**kwargs)
            case SearchAction.SEARCH:
                return self.get_search(**kwargs)
            case _:
                raise InvalidAction(f'Invalid Action `{action}`')

    @staticmethod
    def get_summary(
            query: str | None = None,
            sentences: int | None = None,
            language: str | None = None
    ):

        """
            params:
                query(str):Filter groups by name with this string.
                sentences(int):if set, return the first `sentences` sentences (can be no greater than 10).
                language(str):Set `prefix` to one of the two letter prefixes found
        """


        if language:
            wikipedia.set_lang(language)

        result = wikipedia.summary(query, sentences=sentences)
        return result

    @staticmethod
    def get_search(
            query: str | None = None,
            results: int | None = None,
            language: str | None = None
    ):

        """
            params:
                query(str):Filter groups by name with this string.
                results(int):the maximum number of results returned
                language(str):Set `prefix` to one of the two letter prefixes found

        """

        if language:
            wikipedia.set_lang(language)

        results = wikipedia.search(query, results=results)
        return results

    async def ahandle(
            self,
            *,
            action: str | Enum, **kwargs
    ) -> Any:

        """
            params:
                action(str): Give an action what has given in the Enum.
        """


        if isinstance(action, str):
            action = action.lower()
        match action:
            case SearchAction.SUMMARY:
                return await sync_to_async(self.get_summary, **kwargs)
            case SearchAction.SEARCH:
                return await sync_to_async(self.get_search, **kwargs)
            case _:
                raise InvalidAction(f'Invalid Action `{action}`')
