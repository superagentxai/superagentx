from superagentx.handler.base import BaseHandler

from crawl4ai import AsyncWebCrawler


class ScrapeHandler(BaseHandler):
    """
       This handler class for scrap content from given website using crawl4ai.
       This class extends BaseHandler and defines the interface for extract all content,
       such as text, images, and links.
    """

    def __dir__(self):
        return (
            'scrap_content'
        )

    def __init__(
            self,
            *,
            domain_url: str
    ):
        self.domain_url = domain_url

    async def scrap_content(self):
        """
           Asynchronously scrap text or content based on the given url using crawl4ai.
           This method executes and return content of url.

           Returns:
              It will return the 'text content' of given url.

       """
        async with AsyncWebCrawler(verbose=True) as crawler:
            result = await crawler.arun(
                url=self.domain_url
            )
            return result.markdown
