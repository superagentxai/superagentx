import os
import json
import aiohttp

from agentx.handler.base import BaseHandler


class SerperDevToolHandler(BaseHandler):

    def __init__(self):
        self.search_url: str = "https://google.serper.dev/search"

    async def search(self, *, query: str, total_results: int = 10):
        """
        Serper is a powerful real-time search engine tool API that provides structured data from Google search engine results.
        This tool is designed to perform a semantic search for a specified query from a text's content across the internet. It utilizes the serper.dev API to fetch and display the most
        relevant search results based on the query provided by the user.

        @param query: Query text to search in Serper Dev service
        @param total_results: Number of results
        @return: List of results
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

    def __dir__(self):
        return [
            'search'
        ]
