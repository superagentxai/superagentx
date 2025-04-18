import asyncio
import json
import logging

from superagentx.computer_use.browser.context import BrowserContext
from superagentx.computer_use.browser.models import ActionResult
from superagentx.computer_use.browser.state import TabInfo
from superagentx.computer_use.browser.utils import time_execution_sync
from superagentx.handler.base import BaseHandler
from superagentx.handler.decorators import tool
from superagentx.llm import LLMClient, ChatCompletionParams

logger = logging.getLogger(__name__)

element = """
    (xpath) => {
        const select = document.evaluate(xpath, document, null,
            XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
        if (!select) return null;

        return {
            options: Array.from(select.options).map(opt => ({
                text: opt.text, //do not trim, because we are doing exact match in select_dropdown_option
                value: opt.value,
                index: opt.index
            })),
            id: select.id,
            name: select.name
        };
    }
"""


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
    async def search_google(
            self,
            *,
            query: str,

    ) -> ActionResult:
        """
        Executes a Google search in the current tab with a precise and well-structured query, mimicking human search behavior. Ensures clarity and relevance by avoiding vague, overly broad, or excessively long queries, prioritizing the most essential keywords for optimal results.

        Args:
        @param query: A concise and specific search query that prioritizes the most relevant keywords to yield accurate search results. Avoid overly broad or ambiguous terms.

        """
        page = await self.browser_context.get_current_page()
        await page.goto(f'https://www.google.com/search?q={query}&udm=14')
        await page.wait_for_load_state()
        msg = f'🔍  Searched for "{query}" in Google'
        logger.info(msg)
        return ActionResult(extracted_content=msg, include_in_memory=True)

    @staticmethod
    async def _is_login_page(page):

        # Quick checks
        url = page.url.lower()
        if any(keyword in url for keyword in ["login", "signin", "auth", "authenticate"]):
            return True

        # Look for input fields with common login field names
        has_login_fields = await page.query_selector('input[type="password"]') is not None
        logger.info(f"Has Login Fields: {has_login_fields}")
        if has_login_fields:
            return True

        # Look for forms that might be login forms
        forms = await page.query_selector_all("form")
        for form in forms:
            html = await form.inner_html()
            if any(word in html.lower() for word in ["username", "email", "password", "sign in", "login"]):
                return True

        return False

    @tool
    async def go_to_url(
            self,
            url: str
    ):
        """
        Navigates to the specified URL in the current tab.

        Args:
            url (str):
                The URL to navigate to.

        Returns:
            None

        """
        page = await self.browser_context.get_current_page()
        await page.goto(url)
        await page.wait_for_load_state()
        msg = f'🔗  Navigated to {url}'
        logger.info(msg)
        # if not flag:
        #     flag = await self._is_login_page(page)
        # if flag and not success_url:
        #     error_msg = "❗ 'success_url' must be provided when 'flag' is set to True."
        #     logger.error(error_msg)
        #     return ActionResult(
        #         is_done=True,
        #         extracted_content=error_msg,
        #         include_memory=True
        #     )
        #
        # if flag and success_url:
        #     timeout = 300000  # 5 minutes
        #     logger.info("Please complete login manually in the browser...")
        #
        #     # Wait indefinitely until login is successful
        #     try:
        #         # Wait for a specific selector to appear
        #         await page.wait_for_url(success_url, timeout=timeout)
        #         msg = "✅ Login complete!"
        #         logger.info(msg)
        #         return ActionResult(
        #             extracted_content=msg,
        #             include_memory=True
        #         )
        #     except Exception as e:
        #         msg = f"❌ Login timeout after {timeout} seconds: {e}"
        #         logger.error(msg)
        #         await self.browser_context.close()
        #         return ActionResult(
        #             is_done=True,
        #             error=msg
        #         )

        return ActionResult(
            extracted_content=msg
        )

    @tool
    async def go_back(self):
        """
        Navigates back to the previous page in the browser history.
        """
        await self.browser_context.go_back()
        msg = '🔙  Navigated back'
        logger.info(msg)
        return ActionResult(extracted_content=msg, include_in_memory=True)

    @tool
    async def wait(self, seconds: int = 60):
        """
        Pauses execution for a specified duration.

        This method is typically used to allow time for page elements to load,
        or to accommodate manual user actions such as login or CAPTCHA.

        **Login/Signin Handling**:
            - When waiting for manual user login, limit total wait time to a maximum of **5 minutes**.
            - Break the wait into shorter intervals (e.g., 30 seconds), and **check for page state changes**
              after each interval using actions like `check_page`.
            - Example usage pattern:
                [
                    {"wait": {"seconds": 60}}
                ]
                Repeat this cycle until login is complete or timeout is reached.
            - If login is not completed after 5 minutes, mark `evaluation_previous_goal` as `Failed`
              and log this state in `memory`.

        Args:
            seconds (int, optional):
                Number of seconds to pause execution. Default is 60 seconds.

        Returns:
            None
        """
        msg = f'🕒  Waiting for {seconds} seconds'
        logger.info(msg)
        await asyncio.sleep(seconds)
        return ActionResult(extracted_content=msg, include_in_memory=True)

    @tool
    async def wait_for_element(self, selector: str, timeout: float = 10000):
        """
        Waits for an element matching the given CSS selector to become visible.

        Args:
            selector (str): The CSS selector of the element.
            timeout (float): The maximum time to wait for the element to be visible (in milliseconds).

        Raises:
            TimeoutError: If the element does not become visible within the specified timeout.
        """
        try:
            await self.browser_context.wait_for_element(selector, timeout)
            msg = f'👀  Element with selector "{selector}" became visible within {timeout}ms.'
            logger.info(msg)
            return ActionResult(extracted_content=msg, include_in_memory=True)
        except Exception as e:
            err_msg = f'❌  Failed to wait for element "{selector}" within {timeout}ms: {str(e)}'
            logger.error(err_msg)
            raise Exception(err_msg)

    @tool
    async def click_element_by_index(self, index: int, xpath: str = None):
        """
        Clicks an element specified by an index within a given XPath.

        Args:
            @param index: The index of the element to be clicked.
            @param xpath : The XPath used to locate the elements (default is `None`).
        """
        session = await self.browser_context.get_session()

        if index not in await self.browser_context.get_selector_map():
            raise Exception(f'Element with index {index} does not exist - retry or use alternative actions')

        element_node = await self.browser_context.get_dom_element_by_index(index)
        initial_pages = len(session.context.pages)

        # if element has file uploader then dont click
        if await self.browser_context.is_file_uploader(element_node):
            msg = f'Index {index} - has an element which opens file upload dialog. To upload files please use a specific function to upload files '
            logger.info(msg)
            return ActionResult(extracted_content=msg, include_in_memory=True)
        msg = None

        try:
            download_path = await self.browser_context._click_element_node(element_node)
            if download_path:
                msg = f'💾  Downloaded file to {download_path}'
            else:
                msg = f'🖱️  Clicked button with index {index}: {element_node.get_all_text_till_next_clickable_element(max_depth=2)}'

            logger.info(msg)
            logger.debug(f'Element xpath: {element_node.xpath}')
            logger.info(f"Number of pages: {len(session.context.pages)}")
            if len(session.context.pages) > initial_pages:
                new_tab_msg = 'New tab opened - switching to it'
                msg += f' - {new_tab_msg}'
                logger.info(new_tab_msg)
                await self.browser_context.switch_to_tab()
            return ActionResult(extracted_content=msg, include_in_memory=True)
        except Exception as e:
            logger.warning(f'Element not clickable with index {index} - most likely the page changed')
            return ActionResult(error=str(e))

    @tool
    async def click_element(self,
                            index: int
                            ):
        """
        Clicks an element at the specified index in the DOM.

        Args:
            @param index: The index of the element to be clicked.

        """
        try:
            state = await self.browser_context.get_state()
            await time_execution_sync('remove_highlight_elements')(self.browser_context.remove_highlights)()

            node_element = state.selector_map[int(index)]

            page = await self.browser_context.get_current_page()

            # check if index of selector map are the same as index of items in dom_items
            await self.browser_context._click_element_node(node_element)

            await page.wait_for_load_state()

            # tabs: list[TabInfo] = await self.browser_context.get_tabs_info()
            # last_tab = tabs[-1]
            # logger.info(f"Tabs: {tabs}")
            # await self.browser_context.switch_to_tab(last_tab.page_id)
            msg = f"Clicked Element Successfully"
            return ActionResult(extracted_content=msg, include_in_memory=True)
        except Exception as ex:
            msg = f"Click Element failed {index}: {ex}"
            logger.info(msg)
            return ActionResult(error=msg)

    @tool
    async def open_new_tab(
            self,
            *,
            url: str,

    ):
        """
        Opens a given URL in a new browser tab.

        Args:
            @param url: The URL to be opened in a new tab.
        """
        await self.browser_context.create_new_tab(url)
        msg = f'🔗  Opened new tab with {url}'
        logger.info(msg)
        return ActionResult(extracted_content=msg, include_in_memory=True)

    @tool
    async def input_text(
            self,
            index: int,
            text: str
    ):
        """
        Input text into an input interactive element
        Args:
            @param index: The index of the input element to interact with.
            @param text: The text to input into the selected element.
        """
        try:
            state = await self.browser_context.get_state()
            # await time_execution_sync('remove_highlight_elements')(self.browser_context.remove_highlights)()

            node_element = state.selector_map[int(index)]
            # await self.wait(seconds=3)
            await self.browser_context._input_text_element_node(node_element, text)
            msg = f'⌨️  Input data into index {index}'
            logger.info(msg)
            logger.debug(f'Element xpath: {node_element.xpath}')
            return ActionResult(extracted_content=msg, include_in_memory=True)
        except Exception as ex:
            msg = f'⌨️  Content was Failed input into the text box.{ex}'
            logger.info(msg)
            return ActionResult(error=msg)

    @tool
    async def extract_content(
            self,
            goal: str,
    ):
        """
        Extract page content to retrieve specific information from the page, e.g. all company names, a specific
        description, all information about, links with companies in structured format or simply links

        Args:
            @param goal: The extraction goal specifying what information should be retrieved.
        """
        page = await self.browser_context.get_current_page()
        import markdownify

        strip = ['a', 'img']

        content = markdownify.markdownify(await page.content(), strip=strip)

        # manually append iframe text into the content so it's readable by the LLM (includes cross-origin iframes)
        for iframe in page.frames:
            if iframe.url != page.url and not iframe.url.startswith('data:'):
                content += f'\n\nIFRAME {iframe.url}:\n'
                content += markdownify.markdownify(await iframe.content())

        prompt = ('Your task is to extract the content of the page. You will be given a page and a goal and you should '
                  'extract all relevant information around this goal from the page. If the goal is vague, summarize '
                  'the page. Respond in json format. Extraction goal: {goal}, Page: {page}')
        # template = PromptTemplate(input_variables=['goal', 'page'], template=prompt)
        _prompt = prompt.format(goal=goal, page=content)
        messages = [
            {
                "role": "system",
                "content": "You are the data extractor and give into the json format."
            },
            {
                "role": "user",
                "content": _prompt
            }
        ]
        chat_completion_params = ChatCompletionParams(
            messages=messages
        )
        try:
            output = await self.llm.achat_completion(chat_completion_params=chat_completion_params)
            msg = f'📄  Extracted from page\n: {output.choices[0].message.content}\n'
            logger.debug(msg)
            return ActionResult(extracted_content=msg, include_in_memory=True)
        except Exception as e:
            logger.info(f'Error extracting content: {e}')
            msg = f'📄  Extracted from page\n: {content}\n'
            logger.info(msg)
            return ActionResult(extracted_content=msg)

    @tool
    async def scroll_down(self, amount: int = None):
        """
        Scroll down the page by pixel amount - if no amount is specified, scroll down one page

        Args:
            @param amount: The number of pixels to scroll. If None, scroll down/up one page
        """
        page = await self.browser_context.get_current_page()
        if amount is not None:
            await page.evaluate(f'window.scrollBy(0, {amount});')
        else:
            await page.evaluate('window.scrollBy(0, window.innerHeight);')

        amount = f'{amount} pixels' if amount is not None else 'one page'
        msg = f'🔍  Scrolled down the page by {amount}'
        logger.info(msg)
        return ActionResult(
            extracted_content=msg,
            include_in_memory=True,
        )

    @tool
    async def scroll_up(self, amount: int):
        """
        Scroll up the page by pixel amount - if no amount is specified, scroll up one page
        """
        page = await self.browser_context.get_current_page()
        if amount is not None:
            await page.evaluate(f'window.scrollBy(0, -{amount});')
        else:
            await page.evaluate('window.scrollBy(0, -window.innerHeight);')

        amount = f'{amount} pixels' if amount is not None else 'one page'
        msg = f'🔍  Scrolled up the page by {amount}'
        logger.info(msg)
        return ActionResult(
            extracted_content=msg,
            include_in_memory=True,
        )

    @tool
    async def send_keys(self, keys: str):
        """
        Send strings of special keys like Escape,Backspace, Insert, PageDown, Delete, Enter, Shortcuts such as
        `Control+o`, `Control+Shift+T` are supported as well. This gets used in keyboard.press.
        """
        page = await self.browser_context.get_current_page()

        try:
            await page.keyboard.press(keys)
        except Exception as e:
            if 'Unknown key' in str(e):
                # loop over the keys and try to send each one
                for key in keys:
                    try:
                        await page.keyboard.press(key)
                    except Exception as e:
                        logger.debug(f'Error sending key {key}: {str(e)}')
                        raise e
            else:
                raise e
        msg = f'⌨️  Sent keys: {keys}'
        logger.info(msg)
        return ActionResult(extracted_content=msg, include_in_memory=True)

    @tool
    async def scroll_to_text(self, text: str):  # type: ignore
        """
        If you don't find something which you want to interact with, scroll to it
        """
        page = await self.browser_context.get_current_page()
        try:
            # Try different locator strategies
            locators = [
                page.get_by_text(text, exact=False),
                page.locator(f'text={text}'),
                page.locator(f"//*[contains(text(), '{text}')]"),
            ]

            for locator in locators:
                try:
                    # First check if element exists and is visible
                    if await locator.count() > 0 and await locator.first.is_visible():
                        await locator.first.scroll_into_view_if_needed()
                        await asyncio.sleep(0.5)  # Wait for scroll to complete
                        msg = f'🔍  Scrolled to text: {text}'
                        logger.info(msg)
                        return ActionResult(extracted_content=msg, include_in_memory=True)
                except Exception as e:
                    logger.debug(f'Locator attempt failed: {str(e)}')
                    continue

            msg = f"Text '{text}' not found or not visible on page"
            logger.info(msg)
            return ActionResult(extracted_content=msg, include_in_memory=True)

        except Exception as e:
            msg = f"Failed to scroll to text '{text}': {str(e)}"
            logger.error(msg)
            return ActionResult(error=msg, include_in_memory=True)

    # @tool
    # async def login(self, login_url: str, success_indicator: str):
    #     """
    #     Opens the login page and waits until the user manually logs in.
    #
    #     Args:
    #         login_url (str): The login page URL.
    #         success_indicator (str): A CSS selector or URL pattern that indicates successful login.
    #     """
    #     page = await self.browser_context.get_current_page()
    #
    #     await page.goto(login_url)
    #     logger.info("Please complete login manually in the browser...")
    #
    #     # Wait indefinitely until login is successful
    #     try:
    #         if success_indicator.startswith("http"):
    #             # Wait for a URL pattern
    #             await page.wait_for_url(success_indicator, timeout=0)
    #         else:
    #             # Wait for a specific selector to appear
    #             await page.wait_for_selector(success_indicator, timeout=0)
    #
    #         logger.info("Login complete! Continuing with the next steps...")
    #
    #     except Exception as e:
    #         logger.error(f"Error waiting for login to complete: {e}")

    # @tool
    # async def get_dropdown_options(index: int) -> ActionResult:
    #     """Get all options from a native dropdown"""
    #     page = await self.browser_context.get_current_page()
    #     selector_map = await self.browser_context.get_selector_map()
    #     dom_element = selector_map[index]
    #
    #     try:
    #         # Frame-aware approach since we know it works
    #         all_options = []
    #         frame_index = 0
    #
    #         for frame in page.frames:
    #             try:
    #                 options = await frame.evaluate(element,dom_element.xpath)
    #
    #                 if options:
    #                     logger.debug(f'Found dropdown in frame {frame_index}')
    #                     logger.debug(f'Dropdown ID: {options["id"]}, Name: {options["name"]}')
    #
    #                     formatted_options = []
    #                     for opt in options['options']:
    #                         # encoding ensures AI uses the exact string in select_dropdown_option
    #                         encoded_text = json.dumps(opt['text'])
    #                         formatted_options.append(f'{opt["index"]}: text={encoded_text}')
    #
    #                     all_options.extend(formatted_options)
    #
    #             except Exception as frame_e:
    #                 logger.debug(f'Frame {frame_index} evaluation failed: {str(frame_e)}')
    #
    #             frame_index += 1
    #
    #         if all_options:
    #             msg = '\n'.join(all_options)
    #             msg += '\nUse the exact text string in select_dropdown_option'
    #             logger.info(msg)
    #             return ActionResult(extracted_content=msg, include_in_memory=True)
    #         else:
    #             msg = 'No options found in any frame for dropdown'
    #             logger.info(msg)
    #             return ActionResult(extracted_content=msg, include_in_memory=True)
    #
    #     except Exception as e:
    #         logger.error(f'Failed to get dropdown options: {str(e)}')
    #         msg = f'Error getting options: {str(e)}'
    #         logger.info(msg)
    #         return ActionResult(extracted_content=msg, include_in_memory=True)
