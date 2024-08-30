from enum import Enum
from typing import Any
from agentx.handler.base import BaseHandler
from agentx.handler.wikipedia.exceptions import InvalidAction

import wikipedia


class SearchAction(str, Enum):
    SUMMARY = "summary"
    SEARCH = "search"
    PAGE = "page"


class Wikipedia(BaseHandler):

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
            *,
            action: str | Enum,
            **kwargs
    ) -> Any:
        match action.lower():
            case SearchAction.SUMMARY:
                self.get_summary(**kwargs)
            case SearchAction.SEARCH:
                self.get_search(**kwargs)
            case SearchAction.PAGE:
                self.get_page(**kwargs)
            case _:
                raise InvalidAction(f'Invalid Action `{action}`')

    def get_summary(self,
                    query: str | None = None,
                    sentences: int | None = None,
                    language: str | None = None
                    ) -> Any:
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

    def get_page(self,
                 query
                 ):
        print("query---->", query)
        results = wikipedia.page(query)
        # print(results)
        return results
