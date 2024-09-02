from enum import Enum
from typing import Any

import wikipedia

from agentx.handler.base import BaseHandler
from agentx.handler.wikipedia.exceptions import InvalidAction


class SearchAction(str, Enum):
    SUMMARY = "summary"
    SEARCH = "search"


class WikipediaHandler(BaseHandler):

    def __init__(
            self,
            action: str,
            query: str,
            sentences: int
    ):
        self.action = action
        self.query = query
        self.sentences = sentences

    def handle(
            self,
            action: str | Enum,
            *args,
            **kwargs
    ) -> Any:
        match action.lower():
            case SearchAction.SUMMARY:
                self.get_summary(**kwargs)
            case SearchAction.SEARCH:
                self.get_search(**kwargs)
            case _:
                raise InvalidAction(f'Invalid Action `{action}`')

    def get_summary(self,
                    query: str | None = None,
                    sentences: int | None = None,
                    language: str | None = None
                    ):
        if language:
            wikipedia.set_lang(language)

        result = wikipedia.summary(query, sentences=sentences)
        print(result)
        return result

    def get_search(self,
                   query: str | None = None,
                   results: int | None = None,
                   language: str | None = None
                   ):
        if language:
            wikipedia.set_lang(language)

        results = wikipedia.search(query, results=results)
        print(results)
        return results

    async def ahandle(self, *, action: str | Enum, **kwargs) -> Any:
        pass
