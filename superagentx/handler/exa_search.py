import os

from exa_py import Exa

from superagentx.handler.base import BaseHandler
from superagentx.handler.decorators import tool
from superagentx.utils.helper import sync_to_async


class ExaHandler(BaseHandler):
    """
       A handler class for managing interactions with an Exa database.
       This class extends BaseHandler and provides methods to perform various database operations,
       such as executing queries, managing tables, and handling data transactions in an Exa environment.
    """

    def __init__(
            self,
            api_key: str | None = None
    ):
        super().__init__()
        api_key = api_key or os.getenv("EXA_API_KEY")
        self.exa = Exa(api_key=api_key)

    @tool
    async def search_contents(
            self,
            *,
            query: str,
            use_autoprompt: bool,
            num_results: int = 10,
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
        if not search_type:
            search_type = "auto"

        return await sync_to_async(
            self.exa.search_and_contents,
            query=query,
            type=search_type,
            use_autoprompt=use_autoprompt,
            num_results=num_results,
            )
