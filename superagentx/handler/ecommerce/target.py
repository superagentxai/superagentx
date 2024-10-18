import aiohttp
import logging

from superagentx.handler.base import BaseHandler

logger = logging.getLogger(__name__)


class TargetHandler(BaseHandler):
    base_url: str = "https://target-com-shopping-api.p.rapidapi.com"

    def __init__(
            self,
            *,
            api_key: str,
            top_items: int | None = None
    ):

        """
            Initializes the Target.com shopping handler.

            This handler is used to interact with the Target.com shopping API, allowing for
            operations such as searching for products, retrieving details about items, and
            managing shopping-related activities. It requires an API key for authentication.

            Args:
                api_key (str): The API key used to authenticate requests to the Target.com API.
                top_items (int | None, optional): The number of top items to retrieve or
                    process. If not provided, the default behavior is used.

        """

        self.api_key = api_key
        self.top_items = top_items
        if not self.top_items:
            self.top_items = 5

    async def _retrieve(
            self,
            *,
            endpoint: str,
            params: dict
    ):

        """
            Asynchronously retrieves data from a Target.com API endpoint.

            This internal method is used to send an asynchronous request to a specified
            Target.com API endpoint, using the given query parameters. It facilitates
            interaction with the Target.com shopping API to perform tasks such as fetching
            product details, search results, or other relevant information.

            Args:
                endpoint (str): The specific API endpoint to send the request to, which
                    corresponds to a Target.com service.
                params (dict): A dictionary of parameters to be included in the API request.
                    These parameters may include filters, search terms, or pagination options.

            Returns:
                The response data from the API, typically in JSON format, containing the
                requested information.

            Raises:
                An exception if the request fails, encounters network issues, or if the API
                returns an error response.
        """

        _url = f'{self.base_url}/{endpoint.strip("/")}'
        logger.info(f"{_url}")
        headers = {
            'x-rapidapi-key': self.api_key,
            'x-rapidapi-host': "target-com-shopping-api.p.rapidapi.com"
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    url=_url,
                    headers=headers,
                    params=params
            ) as resp:
                return await resp.json()

    async def product_search(
            self,
            *,
            query: str
    ):

        """
        Searches for products on Target based on the given keyword.

        This method allows you to find products on Target by using a search term such as
        "blender" or "smartphone." It retrieves a list of items that match your query, along
        with key product details like the product name, price, ratings, availability, and
        customer reviews.

        Args:
            query (str): The word or phrase you want to search for on Target.

        Returns:
            A list of products that match your search term, including information such as
            product name, price, ratings, and other relevant details.
        """

        _endpoint = f"product_search"
        params = {
            "store_id": "1122",
            "keyword": query
        }
        res = await self._retrieve(
            endpoint=_endpoint,
            params=params
        )
        if res:
            return res

    def __dir__(self):
        return (
            'product_search',
        )
