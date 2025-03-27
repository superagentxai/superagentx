from superagentx.handler.base import BaseHandler
from superagentx.handler.decorators import tool
from superagentx.computer_use.browser.context import BrowserContext

import logging

logger = logging.getLogger(__name__)


class DomHandler(BaseHandler):

    def __init__(self):
        super().__init__()

    @tool
    async def google_search(self, *, query: str, browser_context: BrowserContext):
        """
        Search the query in Google in the current tab, the query should be a search query like humans search in
        Google, concrete and not vague or super long. More the single most important items.
        """
        page = await browser_context.get_current_page()
        await page.goto(f'https://www.google.com/search?q={query}&udm=14')
        await page.wait_for_load_state()
        msg = f'🔍  Searched for "{query}" in Google'
        logger.info(msg)

