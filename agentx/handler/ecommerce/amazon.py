import aiohttp
import logging

from agentx.handler.base import BaseHandler
from agentx.utils.helper import iter_to_aiter

logger = logging.getLogger(__name__)


class AmazonHandler(BaseHandler):
    base_url: str = "https://real-time-amazon-data.p.rapidapi.com"

    def __init__(
            self,
            api_key: str,
            page: int,
            country: str,
            sort_by: str,
            product_condition: str,
            is_prime: str,
            deals_and_discounts: str

    ):

        self.api_key = api_key
        self.page = page
        self.country = country
        self.sort_by = sort_by
        self.product_condition = product_condition
        self.is_prime = is_prime
        self.deals_and_discounts = deals_and_discounts


    async def _retrieve(
            self,
            endpoint: str,
            params: dict
    ):
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

    async def _construct_data(self, datas: list):
        # _review_data = []
        async for data in iter_to_aiter(datas):
            if data:
                asin_id = data.get("asin")
                reviews = await self.product_reviews(asin_id)
                if reviews:
                    review_data = reviews.get("data")
                    if review_data and review_data.get("asin") == asin_id:
                        _reviews = review_data.get("reviews")
                        data["_reviews"] = _reviews
                        yield data
                        # _review_data.append(data)
        # yield _review_data


    async def search_product(self, query:str):
        _endpoint = f"search"
        params = {
            "query": query
        }
        res = await self._retrieve(_endpoint, params)
        if res and res.get("data"):
            data = res.get("data").get("products")
            return self._construct_data(data)

    async def product_reviews(self, asin:str):
        _endpoint = f"product-reviews"
        params = {
            "asin": asin
        }
        return await self._retrieve(_endpoint, params)

    def __dir__(self):
        return (
            'search_product',
            'product-reviews'
        )



