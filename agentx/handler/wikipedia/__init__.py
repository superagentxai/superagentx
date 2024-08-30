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
                pass
            case SearchAction.PAGE:
                pass
            case _:
                raise InvalidAction(f'Invalid Action `{action}`')

    def get_summary(self,
                    query,
                    sentences
                    ):
        result = wikipedia.summary(query, sentences=sentences)
        return result
        print(result)
