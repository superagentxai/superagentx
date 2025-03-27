from superagentx.computer_use.browser.context import BrowserContext
from superagentx.handler.base import BaseHandler
from superagentx.handler.decorators import tool
from superagentx.llm import LLMClient
import json


class BrowserHandler(BaseHandler):
    """
    The Browser Handler is a specialized module designed to interact with various HTML DOM elements by performing
    a range of automated web actions. It supports multiple event-driven operations, including:

    - **Search Action**: Simulates a search query by interacting with input fields and triggering relevant search events.
    - **Click Action**: Automates mouse click events on buttons, links, and other clickable elements.
    - **Extract Action**: Retrieves and processes data from web pages by extracting text, attributes, or HTML content.
    - **Scroll Up Action**: Programmatically scrolls the webpage upwards to reveal additional content.
    - **Scroll Down Action**: Scrolls down on a webpage, enabling interaction with dynamically loaded elements.

    These functionalities are exposed as tools that can be invoked using the Large Language Model (LLM) tool-calling
    feature, enabling seamless automation of web interactions within AI-driven workflows.
    """

    def __init__(self, llm: LLMClient, browser_context: BrowserContext):
        super().__init__()
        self.llm = llm
        self.browser_context = browser_context

    @tool
    async def rpa_browser_action(self, *, action_arg: str):
        try:
            pass
        except KeyboardInterrupt:
            print("Stopping execution...")

    @tool
    async def search_web(
            self,
            *,
            query: str,

    ):
        """
        Perform a Google search in the current tab using a clear, concise, and specific query—just as a human would.
        Avoid vague, overly broad, or excessively long queries. Prioritize the most important keyword or phrase.

        :param query: Search Query
        :return:

        """
        page = await self.browser_context.get_current_page()
        await page.goto(f'https://www.google.com/search?q={query}&udm=14')
        await page.wait_for_load_state()

    @tool
    async def open_new_tab(
            self,
            *,
            url: str,

    ):
        """
        Open url in new tab
        :param url:
        :return:
        """
        await self.browser_context.create_new_tab(url)
