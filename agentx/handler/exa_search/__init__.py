from enum import Enum
from typing import Any

from exa_py import Exa

from agentx.handler.base import BaseHandler
from agentx.handler.exa_search.exceptions import InvalidExaAction
from agentx.utils.helper import sync_to_async


class ExaAction(str, Enum):
    SEARCH_CONTENTS = "search_contents"


class ExaHandler(BaseHandler):

    def __init__(
            self,
            api_key: str | None = None
    ):

        self.exa = Exa(api_key=api_key)

    def handle(
            self,
            *,
            action: str | Enum,
            **kwargs
    ) -> Any:
        """Perform a search with an Exa prompt-engineered query and retrieve a list of relevant results.

        params:
            action(str): Give an action what has given in the Enum.

        """

        if isinstance(action, str):
            action = action.lower()
        match action:
            case ExaAction.SEARCH_CONTENTS:
                return self.search_contents(**kwargs)
            case _:
                raise InvalidExaAction(f"Invalid exa action '{action}'")

    async def ahandle(
            self,
            *,
            action: str | Enum,
            **kwargs
    ) -> Any:

        """Perform a search with an Exa prompt-engineered query and retrieve a list of relevant results.

           params:
               action(str): Give an action what has given in the Enum.

        """

        if isinstance(action, str):
            action = action.lower()
        match action:
            case ExaAction.SEARCH_CONTENTS:
                return await self.asearch_contents(**kwargs)
            case _:
                raise InvalidExaAction(f"Invalid exa action '{action}'")

    def search_contents(
            self,
            *,
            query: str,
            use_autoprompt: bool,
            num_results: int | None = 10,
            search_type: str | None = None

    ):
        """Perform a search with an Exa prompt-engineered query and retrieve a list of relevant results.

        params:
            query (str): The query string.
            num_results (int, optional): Number of search results to return. Defaults to 10.
            use_autoprompt (bool, optional): If true, convert query to a Exa query. Defaults to False.
            type (str, optional): The type of search, 'keyword' or 'neural'. Defaults to "auto".

        """
        if search_type is None:
            search_type = "auto"

        result = self.exa.search_and_contents(
            query=query,
            type=search_type,
            use_autoprompt=use_autoprompt,
            num_results=num_results
        )
        return result

    async def asearch_contents(
            self,
            *,
            query: str,
            use_autoprompt: bool,
            num_results: int | None = 10,
            search_type: str | None = None
    ):
        """Perform a search with an Exa prompt-engineered query and retrieve a list of relevant results.

           params:
               query (str): The query string.
               num_results (int, optional): Number of search results to return. Defaults to 10.
               use_autoprompt (bool, optional): If true, convert query to a Exa query. Defaults to False.
               type (str, optional): The type of search, 'keyword' or 'neural'. Defaults to "auto".

        """
        if search_type is None:
            search_type = "auto"

        result = await sync_to_async(
            self.exa.search_and_contents,
            query=query,
            type=search_type,
            use_autoprompt=use_autoprompt,
            num_results=num_results,
            )
        return result
