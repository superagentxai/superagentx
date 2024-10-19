from superagentx.handler.base import BaseHandler

from crawl4ai import AsyncWebCrawler

from superagentx.utils.helper import iter_to_aiter


class ScrapeHandler(BaseHandler):
    """
          The `ScrapeHandler` class extends the `BaseHandler` and is responsible for
        handling the scraping of content from websites or other data sources. It
        encapsulates the logic for initiating, processing, and managing scraped
        data in an efficient and scalable way, often for use in an asynchronous
        environment.

        In addition to basic scraping functionalities, it also provides methods for:
        - Managing request headers, cookies, and other HTTP request configurations.
        - Handling paginated content and dynamic data loading.
        - Processing and storing the scraped content.
    """

    def __init__(
            self,
            *,
            domain_urls: list[str]
    ):
        """
        Initializes a new instance of the ScrapeHandler class.

        Args:
            domain_urls (list[str]): A list of domain URLs to be scraped.
        
        """
        self.domain_url = domain_urls

    async def scrap_content(self):

        """
            This method fetches and processes the content from the target website or data source
            using an asynchronous approach to ensure non-blocking operations.

            Returns:
                Parsed content (could be a list, dict, or other structure depending on implementation).

       """
        async with AsyncWebCrawler(verbose=True) as crawler:
            results = await crawler.arun_many(
                urls=self.domain_url
            )
            if results:
                return [
                    res.markdown async for res in iter_to_aiter(results) if res
                ]

    def __dir__(self):
        return (
            'scrap_content',
        )
