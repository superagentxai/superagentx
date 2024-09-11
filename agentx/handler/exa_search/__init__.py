import os
from enum import Enum
from typing import Any

from exa_py import Exa

from agentx.handler.base import BaseHandler
from agentx.handler.exa_search.exceptions import InvalidEXAAction
from agentx.utils.helper import sync_to_async


class EXAAction(str, Enum):
    SEARCH_CONTENTS = "search_contents"


class ExaHandler(BaseHandler):

    def __init__(
            self,
            api_key: str | None = None
    ):

        api_key = api_key if api_key else os.getenv("EXA_API_KEY")
        self.exa = Exa(api_key=api_key)

    def handle(
            self,
            *args,
            action: str | Enum,
            **kwargs
    ) -> Any:
        if isinstance(action, str):
            action = action.lower()
        match action:
            case EXAAction.SEARCH_CONTENTS:
                return self.search_contents(*args, **kwargs)
            case _:
                raise InvalidEXAAction(f"Invalid exa action '{action}'")

    async def ahandle(
            self,
            *,
            action: str | Enum,
            **kwargs
    ) -> Any:
        if isinstance(action, str):
            action = action.lower()
        match action:
            case EXAAction.SEARCH_CONTENTS:
                return await self.asearch_contents(**kwargs)
            case _:
                raise InvalidEXAAction(f"Invalid exa action '{action}'")

    def search_contents(
            self,
            query: str,
            type: str,
            use_autoprompt: bool,
            num_results: int

    ):
        result = self.exa.search_and_contents(
            query=query,
            type=type,
            use_autoprompt=use_autoprompt,
            num_results=num_results
        )
        return result

    async def asearch_contents(
            self,
            *,
            query,
            type,
            use_autoprompt,
            num_results,
    ):
        result = await sync_to_async(self.exa.search_and_contents,
                                     query,
                                     type=type,
                                     use_autoprompt=use_autoprompt,
                                     num_results=num_results,
                                     )
        return result
