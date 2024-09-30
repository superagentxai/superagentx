import aiohttp
import logging

from agentx.handler.base import BaseHandler
from agentx.utils.helper import iter_to_aiter

logger = logging.getLogger(__name__)


class FlipkartHandler(BaseHandler):
    base_url: str = "https://real-time-flipkart-api.p.rapidapi.com"

    def __init__(
            self,
            api_key: str
    ):
        self.api_key = api_key

    async def _retrieve(
            self,
            *,
            endpoint: str,
            params: dict
    ):
        """
        Asynchronously retrieves data from a specified API endpoint with provided query parameters.

        This method is designed to interact with an external API, sending a GET request
        to the specified `endpoint`. It passes the `params` dictionary as query parameters
        for the API call. The method is asynchronous, meaning it should be awaited to
        prevent blocking execution in an event-driven or concurrent environment.

        parameter:
        endpoint (str): The API endpoint from which to retrieve data.
        params (dict): A dictionary of query parameters to include in the request.
        """

        _url = f'{self.base_url}/{endpoint.strip("/")}'
        logger.info(f"{_url}")
        headers = {
            'x-rapidapi-key': self.api_key,
            'x-rapidapi-host': "real-time-flipkart-api.p.rapidapi.com"
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    _url,
                    headers=headers,
                    params=params
            ) as resp:
                return await resp.json()

    async def _construct_data(
            self,
            data: list
    ):
        """
        Asynchronously constructs and processes data from a given list of items.

        This method processes each element in the provided `item` list and transforms it
        into a specific format or structure. The details of the transformation depend on
        the business logic defined within the method. Since the method is asynchronous,
        it is likely interacting with other asynchronous functions or awaiting I/O-bound operations
        such as network requests or file operations.

        parameter:
            item (list):
                A list of items to be processed. Each element in the list represents
                an individual data point or object that will be transformed or processed
                by the method. The content and type of each list element should conform
                to the expected format for proper processing.
        """

        async for item in iter_to_aiter(data):
            if item:
                pid_id = item.get("pid")
                reviews = await self.product_reviews(pid_id)
                if reviews and reviews.get("pid", "") == pid_id:
                    _reviews = reviews.get("reviews")
                    item["_reviews"] = _reviews
                    yield item

    async def product_search(
            self,
            *,
            query: str
    ):
        """
        Asynchronously searches for a product based on a given query string.

        This method performs a search operation to retrieve product data that matches
        the input `query` with the reviews. It sends the query to an external search API or a local database
        and returns relevant product information based on the search results. Since the
        method is asynchronous, it likely involves I/O-bound operations such as making
        network requests to an API or querying a database.

        parameter:
        query (str):
            A string containing the search term or phrase used to find relevant products.
            This could be the product name, a keyword, or any other search criterion
            supported by the underlying data source.
        """

        _endpoint = f"product-search"
        params = {
            "q": query
        }
        res = await self._retrieve(
            endpoint=_endpoint,
            params=params
        )
        if res:
            products = res.get("products") or []
            return self._construct_data(products)

    async def product_reviews(
            self,
            pid: str
    ):
        """
        Asynchronously retrieves reviews for a specific product identified by its product ID (PID).

        This method fetches reviews related to a product based on its unique product identifier (PID).
        The reviews can be pulled from an external API, database, or other data sources that store
        customer feedback and ratings. As the method is asynchronous, it is designed to handle
        I/O-bound operations without blocking the main execution flow, making it suitable for
        applications that require non-blocking I/O such as network requests.

        parameter:
        pid (str):
            The product identifier (PID) for which the reviews are to be retrieved.
            This `pid` should be a valid string that uniquely identifies a product in the
            system, which could vary based on the platform or database in use.
        """
        _endpoint = f"product-details"
        params = {
            "pid": pid
        }
        return await self._retrieve(
            endpoint=_endpoint,
            params=params
        )

    def __dir__(self):
        return (
            'product_search',
            'product_reviews'
        )
