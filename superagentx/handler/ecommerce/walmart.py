import aiohttp
import logging
import urllib.parse
import re

from superagentx.handler.base import BaseHandler
from superagentx.utils.helper import iter_to_aiter

logger = logging.getLogger(__name__)


class WalmartHandler(BaseHandler):
    base_url: str = "https://walmart-product-info.p.rapidapi.com"

    def __init__(
            self,
            *,
            api_key: str,
            top_items: int | None = None
    ):
        """
        Initializes the Walmart.com shopping handler.

        This handler is used to interact with the Walmart.com shopping API, allowing for
        operations such as searching for products, retrieving details about items, and
        managing shopping-related activities. It requires an API key for authentication.

        Args:
            api_key (str): The API key used to authenticate requests to the Walmart.com API.
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
            Asynchronously retrieves data from a Walmart.com API endpoint.

            This internal method is used to send an asynchronous request to a specified
            Walmart.com API endpoint, using the given query parameters. It facilitates
            interaction with the Walmart.com shopping API to perform tasks such as fetching
            product details, search results, or other relevant information.

            Args:
                endpoint (str): The specific API endpoint to send the request to, which
                    corresponds to a Walmart.com service.
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
            'x-rapidapi-host': "walmart-product-info.p.rapidapi.com",
            'Content-Type':'application/json'

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
            Searches for products on Walmart based on the given keyword.

            This method allows you to find products on Walmart by using a search term such as
            "blender" or "smartphone." It retrieves a list of items that match your query, along
            with key product details like the product name, price, ratings, availability, and
            customer reviews.

            Args:
                query (str): The word or phrase you want to search for on Walmart.

            Returns:
                A list of products that match your search term, including information such as
                product name, price, ratings, and other relevant details.
        """

        _endpoint = f"walmart-serp.php"
        params = {
            "url": "https://www.walmart.com/search?q="+urllib.parse.quote(query)
        }
        products = await self._retrieve(
            endpoint=_endpoint,
            params=params
        )
        if products:
            #return [item async for item in self._construct_data(products)]
            return products

    async def product_reviews(
            self,
            url: str
    ):
        """
            Fetches customer reviews for a specific product on Walmart.

            This method allows you to retrieve customer feedback for a product by using its URL
            from Walmart. The reviews include customer ratings, comments, and other feedback
            that can help you evaluate the product's quality and performance based on user
            experiences.

            Args:
                url (str): The URL of the Walmart product for which you want to fetch reviews.

            Returns:
                A list of customer reviews, including details such as ratings and comments, to help
                you understand how customers feel about the product.
        """
        _endpoint = f"details.php"
        params = {
            "url": f"https://www.walmart.com/ip/{url}"
        }
        return await self._retrieve(
            endpoint=_endpoint,
            params=params
        )

    def __dir__(self):
        return (
            'product_search',
            'product_reviews',
        )