import aiohttp
import logging

from agentx.handler.base import BaseHandler

logger = logging.getLogger(__name__)


class TargetHandler(BaseHandler):
    base_url: str = "https://target-com-shopping-api.p.rapidapi.com"

    def __init__(
            self,
            *,
            api_key: str,
            top_items: int = 1
    ):
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
