import os
import json
import aiohttp

from superagentx.handler.base import BaseHandler
from superagentx.handler.decorators import tool


class SerperDevToolHandler(BaseHandler):

    def __init__(self):
        super().__init__()
        self.search_url: str = "https://google.serper.dev/search"

    @tool
    async def search(
            self,
            *,
            query: str,
            total_results: int = 5
    ):
        """
        A tool for performing real-time web searches and retrieving structured results based on the provided query.

        Parameters:
            query(str): The search text or query to find relevant information.
            total_results(int): Number of total results

        Return:
            List of Dict
        """

        payload = json.dumps({
            "q": query
        })

        headers = {
            "X-API-KEY": os.environ["SERPER_API_KEY"],
            "content-type": "application/json",
        }
        results = []
        async with aiohttp.ClientSession() as session:
            async with session.post(
                    self.search_url,
                    headers=headers,
                    data=payload,
            ) as response:
                search_results = await response.json()

                if "organic" in search_results:
                    results = search_results["organic"][: total_results]
                    string = []
                    for result in results:
                        try:
                            string.append(
                                "\n".join(
                                    [
                                        f"Title: {result['title']}",
                                        f"Link: {result['link']}",
                                        f"Snippet: {result['snippet']}",
                                        "---",
                                    ]
                                )
                            )
                        except KeyError:
                            continue
            return results
