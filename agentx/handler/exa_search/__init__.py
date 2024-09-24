from enum import Enum
from typing import Any

from exa_py import Exa

from agentx.handler.base import BaseHandler
from agentx.handler.exa_search.exceptions import InvalidExaAction
from agentx.utils.helper import sync_to_async


class ExaAction(str, Enum):
    SEARCH_CONTENTS = "search_contents"


class ExaHandler(BaseHandler):
    """
       A handler class for managing interactions with an Exa database.
       This class extends BaseHandler and provides methods to perform various database operations,
       such as executing queries, managing tables, and handling data transactions in an Exa environment.
    """

    def __init__(
            self,
            api_key: str
    ):

        self.exa = Exa(api_key=api_key)

    async def handle(
            self,
            *,
            action: str | Enum,
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
            case ExaAction.SEARCH_CONTENTS:
                return await self.search_contents(**kwargs)
            case _:
                raise InvalidExaAction(f"Invalid exa action '{action}'")

    async def search_contents(
            self,
            *,
            query: str,
            use_autoprompt: bool,
            num_results: int | None = 10,
            search_type: str | None = None
    ):
        """
        Asynchronously searches content based on the query, with options to use autoprompt, limit the number of results,
        and filter by search type. Customizes the search experience according to the provided parameters.

        Parameters:
            query (str): The search query string used to find relevant content.
            use_autoprompt (bool): If True, the method will leverage autoprompt suggestions to enhance the search
            results.
            num_results (int | None, optional): The maximum number of search results to return. Defaults to 10.
            If set to None, all available results may be returned.
            search_type (str | None, optional): Specifies the type of search to perform. Defaults to None,
            in which case a general search is performed.

        Returns:
            Any: The search results, which may vary depending on the search type and query.

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

    def __dir__(self):
        return (
            'search_contents'
        )
