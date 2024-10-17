import aiohttp
import logging
import os

from superagentx.handler.base import BaseHandler
from superagentx.utils.helper import iter_to_aiter

logger = logging.getLogger(__name__)


class FlipkartHandler(BaseHandler):
    base_url: str = "https://real-time-flipkart-api.p.rapidapi.com"

    def __init__(
            self,
            api_key: str | None = None,
            top_items: int | None = None
    ):
        self.api_key = api_key or os.getenv('RAPID_API_KEY')
        self.top_items = top_items
        if not self.top_items:
            self.top_items = 5

    async def _retrieve(
            self,
            *,
            endpoint: str,
            params: dict
    ):
        _url = f'{self.base_url}/{endpoint.strip("/")}'
        logger.debug(f"{_url}")
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
        async for item in iter_to_aiter(data):
            if item:
                pid_id = item.get("pid")
                reviews = await self.product_reviews(pid_id)
                if reviews and reviews.get("pid", "") == pid_id:
                    _reviews = reviews.get("reviews")
                    logger.debug(f"Reviews Length: {len(_reviews)}")
                    item["reviews"] = _reviews[:self.top_items]
                    yield item

    async def product_search(
            self,
            *,
            query: str
    ):
        """
        Performs a search on Flipkart for products matching the given query.

        This method takes a search term (like "laptop" or "smartphone") and looks for relevant
        products on Flipkart. It returns a list of products that match the search, along with
        useful information like their prices, ratings, and descriptions.

        Args:
            query (str): The search term you're using to find products on Flipkart.

        Returns:
            A list of products that match the search query. Each product will include details
            such as its name, price, and other relevant information from Flipkart.

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
            return [item async for item in self._construct_data(products[:self.top_items])]

    async def product_reviews(
            self,
            pid: str
    ):
        """
        Fetches reviews for a specific product on Flipkart.

        This method retrieves customer reviews for a product using its product ID (pid). You can
        use this to see what other people are saying about a product, including their ratings
        and feedback.

        Args:
            pid (str): The unique identifier for the product you want to get reviews for.

        Returns:
            A list of reviews, where each review includes the rating, the reviewer's comments,
            and any other details Flipkart provides.
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
