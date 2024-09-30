import aiohttp
import logging

from agentx.handler.base import BaseHandler
from agentx.utils.helper import iter_to_aiter

logger = logging.getLogger(__name__)


class AmazonHandler(BaseHandler):
    base_url: str = "https://real-time-amazon-data.p.rapidapi.com"

    def __init__(
            self,
            *,
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
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": "real-time-amazon-data.p.rapidapi.com"
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
            item: list
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

        async for item in iter_to_aiter(item):
            if item:
                asin_id = item.get("asin")
                reviews = await self.product_reviews(asin_id)
                if reviews:
                    review_data = reviews.get("data")
                    if review_data and review_data.get("asin") == asin_id:
                        _reviews = review_data.get("reviews")
                        item["_reviews"] = _reviews
                        yield item

    async def search_product(
            self,
            *,
            query: str
    ):

        """
        Asynchronously searches for a product based on a given query string.

        This method performs a search operation to retrieve product data that matches
        the input `query`. It sends the query to an external search API or a local database
        and returns relevant product information based on the search results. Since the
        method is asynchronous, it likely involves I/O-bound operations such as making
        network requests to an API or querying a database.

        parameter:
            query (str):
                A string containing the search term or phrase used to find relevant products.
                This could be the product name, a keyword, or any other search criterion
                supported by the underlying data source.

        """

        _endpoint = f"search"
        params = {
            "query": query
        }
        res = await self._retrieve(
            endpoint=_endpoint,
            params=params
        )
        if res:
            data = res.get('data')
            if data:
                products = data.get("products") or []
                return self._construct_data(products)

    async def product_reviews(
            self,
            asin: str
    ):

        """
        Asynchronously retrieves reviews for a specific product identified by its ASIN.

        This method fetches reviews related to a product based on its Amazon Standard
        Identification Number (ASIN). The reviews may be retrieved from an external API
        or a database that stores customer feedback and ratings. Since the method is
        asynchronous, it is designed to handle I/O-bound operations such as making network
        requests or database queries without blocking execution.

        Args:
            asin (str):
                The Amazon Standard Identification Number (ASIN) of the product whose reviews
                are to be retrieved. The ASIN is a unique identifier used by Amazon to track
                products, and it should be a valid string conforming to Amazon's ASIN format.

        """

        _endpoint = f"product-reviews"
        params = {
            "asin": asin
        }
        return await self._retrieve(
            endpoint=_endpoint,
            params=params
        )

    def __dir__(self):
        return (
            'search_product',
            'product_reviews'
        )
