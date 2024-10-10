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
            api_key: str,
            country: str, # US, AU, BR, CA, CN, FR, DE, IN, IT, MX, NL, SG, ES, TR, AE, GB, JP, SA, PL, SE, BE, EG
            top_items: int | None = None
    ):
        self.api_key = api_key
        self.country = country
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
            data: list
    ):
        async for item in iter_to_aiter(data):
            if item:
                asin_id = item.get("asin")
                reviews = await self.product_reviews(asin_id)
                if reviews:
                    review_data = reviews.get("data")
                    if review_data and review_data.get("asin", "") == asin_id:
                        _reviews = review_data.get("reviews")
                        logger.debug(f"Reviews Length: {len(_reviews)}")
                        item["reviews"] = _reviews[:self.top_items]
                        yield item

    async def product_search(
            self,
            *,
            query: str
    ):
        """
        Searches for products on Amazon based on the given keyword.

        This method helps you find products on Amazon by using a search term like "laptop" or
        "headphones." It will return a list of items that match what you're looking for, along
        with important details like the product name, price, ratings, comments, and other feedback from customers.

        Args:
            query (str): The word or phrase you want to search for on Amazon.

        Returns:
            A list of products that match your search term, with information about each item.
        """
        _endpoint = f"search"
        params = {
            "query": query,
            "sort_by": "RELEVANCE",
            "country": self.country
        }
        res = await self._retrieve(
            endpoint=_endpoint,
            params=params
        )
        if res:
            data = res.get('data')
            if data:
                products = data.get("products") or []
                logger.debug(f"Product length: {len(products)}")
                return [item async for item in self._construct_data(products[:self.top_items])]

    async def product_reviews(
            self,
            asin: str
    ):
        """
        Fetches customer reviews for a specific product on Amazon.

        This method allows you to see what other customers are saying about a product by using
        its ASIN (Amazon's unique product identifier). You can use it to get a list of reviews,
        which may include ratings, comments, and other feedback from customers.

        Args:
            asin (str): The unique Amazon product ID for the item you're interested in.

        Returns:
            A list of reviews with details such as customer ratings and comments, helping you
            understand how others feel about the product.
        """
        _endpoint = f"product-reviews"
        params = {
            "asin": asin,
            "sort_by": "TOP_REVIEWS"
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
