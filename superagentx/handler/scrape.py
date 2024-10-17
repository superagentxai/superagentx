from superagentx.handler.base import BaseHandler

from crawl4ai import AsyncWebCrawler


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

    def __dir__(self):
        return (
            'scrap_content',
        )

    def __init__(
            self,
            *,
            domain_url: list
    ):
        self.domain_url = domain_url

    async def scrap_content(self):

        """
            This method fetches and processes the content from the target website or data source
            using an asynchronous approach to ensure non-blocking operations.

            Returns:
                Parsed content (could be a list, dict, or other structure depending on implementation).

       """
        async with AsyncWebCrawler(verbose=True) as crawler:
            result = await crawler.arun_many(
                urls=self.domain_url
            )
            arr=[]
            if result and result[0]:
                for res in result:
                    if res:
                        arr.append(str(res.markdown))
                return arr

