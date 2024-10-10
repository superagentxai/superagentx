import os
from urllib.parse import urlencode
from typing import Sequence, Optional
import logging
import aiohttp

from agentx.handler.base import BaseHandler

logger = logging.getLogger(__name__)


class SerplyJobHandler(BaseHandler):

    def __init__(self, *, location: str = 'US'):
        self.job_search_url: str = "https://api.serply.io/v1/job/search/"
        self.proxy_location: Optional[str] = "US"
        self.headers = {
            "X-API-KEY": os.environ["SERPLY_API_KEY"],
            "User-Agent": "superagentx",
            "X-Proxy-Location": location,
        }

    async def search(self, query: str):
        query_payload = {'q': query}

        url = f"{self.job_search_url}{urlencode(query_payload)}"
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    url,
                    headers=self.headers
            ) as response:

                logger.info(f'Jobs List {await response.json()}')

        pass

    def __dir__(self) -> list[str] | tuple[str] | Sequence[str]:
        pass
