import asyncio
import json
import logging

from superagentx.computer_use.browser.context import BrowserContext
from superagentx.computer_use.browser.models import ToolResult
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
    ) -> ToolResult:
        """
        Executes a Google search in the current tab with a precise and well-structured query, mimicking human search
        behavior. Ensures clarity and relevance by avoiding vague, overly broad, or excessively long queries,
        prioritizing the most essential keywords for optimal results.

        Args:
        @param query: A concise and specific search query that prioritizes the most relevant keywords to yield accurate
        search results. Avoid overly broad or ambiguous terms.

        """
        page = await self.browser_context.get_current_page()
        await page.goto(f'https://www.google.com/search?q={query}&udm=14')
        await page.wait_for_load_state()
        msg = f'🔍  Searched for "{query}" in Google'
        logger.info(msg)
        return ToolResult(extracted_content=msg, include_in_memory=True)

    @tool
    async def go_to_url(
            self,
            url: str
    ) -> ToolResult:
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
        return ToolResult(
            extracted_content=msg
        )

    @tool
    async def go_back(self) -> ToolResult:
        """
        Navigates back to the previous page in the browser history.
        """
        await self.browser_context.go_back()
        msg = '🔙  Navigated back'
        logger.info(msg)
        return ToolResult(extracted_content=msg, include_in_memory=True)

    @tool
    async def wait(
            self,
            seconds: int = 10
    ) -> ToolResult:
        """
        Pauses execution for a specified duration.

        This method is typically used to allow time for page elements to load,
        or to accommodate manual user actions such as login or CAPTCHA.

        **Login/Signin Handling**:
            - When waiting for manual user login, limit total wait time to a maximum of **5 minutes**.
            - Break the wait into shorter intervals (e.g., 10 seconds), and **check for page state changes**
              after each interval using actions like `check_page`.
            - Example usage pattern:
                [
                    {"wait": {"seconds": 10}}
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
        msg = f"🕒 Wait successfully Completed"
        logger.info(msg)
        return ToolResult(extracted_content=msg, include_in_memory=True)

    @tool
    async def click_element_by_index(
            self,
            index: int
    ) -> ToolResult:
        """
        Clicks an element specified by an index within a given XPath.

        Args:
            @param index: The index of the element to be clicked.
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
            return ToolResult(extracted_content=msg, include_in_memory=True)
        msg = None

        try:
            download_path = await self.browser_context._click_element_node(element_node)
            if download_path:
                msg = f'💾  Downloaded file to {download_path}'
            else:
                msg = f'🖱️  Clicked button with index {index}: {element_node.get_all_text_till_next_clickable_element(max_depth=2)}'
            no_of_pages = len(session.context.pages)
            logger.info(msg)
            logger.debug(f'Element xpath: {element_node.xpath}')
            logger.info(f"Number of pages: {no_of_pages}")
            if no_of_pages > initial_pages:
                new_tab_msg = 'New tab opened - switching to it'
                msg += f' - {new_tab_msg}'
                logger.info(new_tab_msg)
                await self.browser_context.switch_to_tab(-1)
            return ToolResult(extracted_content=msg, include_in_memory=True)
        except Exception as e:
            logger.warning(f'Element not clickable with index {index} - most likely the page changed')
            return ToolResult(error=str(e))

    @tool
    async def open_new_tab(
            self,
            *,
            url: str,
    ) -> ToolResult:
        """
        Opens a given URL in a new browser tab.

        Args:
            @param url: The URL to be opened in a new tab.
        """
        await self.browser_context.create_new_tab(url)
        msg = f'🔗  Opened new tab with {url}'
        logger.info(msg)
        return ToolResult(extracted_content=msg, include_in_memory=True)

    @tool
    async def switch_tab(
            self,
            page_id: int
    ) -> ToolResult:
        """
        Switches the browser context to a different tab based on the provided page ID.

        This is useful when multiple tabs are open and you want to interact with a specific one.

        Args:
            page_id (int): The ID of the tab (page) you want to switch to.
        """
        await self.browser_context.switch_to_tab(page_id)
        # Wait for tab to be ready
        page = await self.browser_context.get_current_page()
        await page.wait_for_load_state()
        msg = f'🔄  Switched to tab {page_id}'
        logger.info(msg)
        return ToolResult(extracted_content=msg, include_in_memory=True)

    @tool
    async def close_tab(
            self,
            page_id: int
    ) -> ToolResult:
        await self.browser_context.switch_to_tab(page_id)
        page = await self.browser_context.get_current_page()
        url = page.url
        await page.close()
        msg = f'❌  Closed tab #{page_id} with url {url}'
        logger.info(msg)
        return ToolResult(extracted_content=msg, include_in_memory=True)

    @tool
    async def input_text(
            self,
            index: int,
            text: str,
            has_sensitive: bool = False
    ) -> ToolResult:
        """
        Input text into an input interactive element
        Args:
            @param index: The index of the input element to interact with.
            @param text: The text to input into the selected element.
            @param has_sensitive: Has Sensitive data. Default False
        """
        if index not in await self.browser_context.get_selector_map():
            return ToolResult(error=f'Element index {index} does not exist - retry or use alternative actions')
        try:
            element_node = await self.browser_context.get_dom_element_by_index(index)
            await self.wait(seconds=3)
            await self.browser_context._input_text_element_node(element_node, text=text)
            if not has_sensitive:
                msg = f'⌨️  Input data into index {index} {text}'
            else:
                msg = f'⌨️  Input data into index {index}'
            logger.info(msg)
            logger.debug(f'Element xpath: {element_node.xpath}')
            return ToolResult(extracted_content=msg, include_in_memory=True)
        except Exception as ex:
            msg = f'⌨️  Content was Failed input into the text box.{ex}'
            logger.info(msg)
            return ToolResult(error=msg)

    @tool
    async def extract_content(
            self,
            goal: str,
    ) -> ToolResult:
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
                  'the page. Respond in json format. Extraction goal: {goal}')
        # template = PromptTemplate(input_variables=['goal', 'page'], template=prompt)
        _prompt = prompt.format(goal=goal, page=content)
        messages = [
            {
                "role": "system",
                "content": "You are the data extractor and give into the json format."
            },
            {
                "role": "user",
                "content": [{
                    "type": "text",
                    "text": _prompt
                }, {
                    'type': 'image_url',
                    'image_url': {'url': f'data:image/png;base64,{await self.browser_context.take_screenshot()}'},
                    # , 'detail': 'low'
                }
                ]
            }
        ]
        chat_completion_params = ChatCompletionParams(
            messages=messages
        )
        try:
            output = await self.llm.achat_completion(chat_completion_params=chat_completion_params)
            msg = f'📄  Extracted from page\n: {output.choices[0].message.content}\n'
            logger.info(msg)
            return ToolResult(extracted_content=msg, include_in_memory=True)
        except Exception as e:
            logger.error(f'Error extracting content: {e}')
            msg = f'📄  Failed to extract \n: {content}\n'
            logger.error(msg)
            return ToolResult(extracted_content=msg)

    @tool
    async def scroll_down(
            self,
            amount: int = None
    ) -> ToolResult:
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
        return ToolResult(
            extracted_content=msg,
            include_in_memory=True,
        )

    @tool
    async def scroll_up(
            self,
            amount: int
    ) -> ToolResult:
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
        return ToolResult(
            extracted_content=msg,
            include_in_memory=True,
        )

    @tool
    async def send_keys(
            self,
            keys: str
    ) -> ToolResult:
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
        return ToolResult(extracted_content=msg, include_in_memory=True)

    @tool
    async def scroll_to_text(
            self,
            text: str
    ) -> ToolResult:  # type: ignore
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
                        return ToolResult(extracted_content=msg, include_in_memory=True)
                except Exception as e:
                    logger.debug(f'Locator attempt failed: {str(e)}')
                    continue

            msg = f"Text '{text}' not found or not visible on page"
            logger.info(msg)
            return ToolResult(extracted_content=msg, include_in_memory=True)

        except Exception as e:
            msg = f"Failed to scroll to text '{text}': {str(e)}"
            logger.error(msg)
            return ToolResult(error=msg, include_in_memory=True)

    @tool
    async def get_dropdown_options(
            self,
            index: int
    ) -> ToolResult:
        """
        Retrieve all selectable options from a native dropdown element on a web page.

        This method locates a dropdown element based on its index (order of appearance)
        and extracts all available option values. It is typically used in browser automation
        or scraping contexts where interaction with HTML `<select>` elements is required.

        Args:
            index (int): The zero-based index of the dropdown element on the page.
        """
        page = await self.browser_context.get_current_page()
        selector_map = await self.browser_context.get_selector_map()
        dom_element = selector_map[index]

        try:
            # Frame-aware approach since we know it works
            all_options = []
            frame_index = 0

            for frame in page.frames:
                try:
                    options = await frame.evaluate(
                        """
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
                    """,
                        dom_element.xpath,
                    )

                    if options:
                        logger.debug(f'Found dropdown in frame {frame_index}')
                        logger.debug(f'Dropdown ID: {options["id"]}, Name: {options["name"]}')

                        formatted_options = []
                        for opt in options['options']:
                            # encoding ensures AI uses the exact string in select_dropdown_option
                            encoded_text = json.dumps(opt['text'])
                            formatted_options.append(f'{opt["index"]}: text={encoded_text}')

                        all_options.extend(formatted_options)

                except Exception as frame_e:
                    logger.debug(f'Frame {frame_index} evaluation failed: {str(frame_e)}')

                frame_index += 1

            if all_options:
                msg = '\n'.join(all_options)
                msg += '\nUse the exact text string in select_dropdown_option'
                logger.info(msg)
                return ToolResult(extracted_content=msg, include_in_memory=True)
            else:
                msg = 'No options found in any frame for dropdown'
                logger.info(msg)
                return ToolResult(extracted_content=msg, include_in_memory=True)

        except Exception as e:
            logger.error(f'Failed to get dropdown options: {str(e)}')
            msg = f'Error getting options: {str(e)}'
            logger.info(msg)
            return ToolResult(extracted_content=msg, include_in_memory=True)

    @tool
    async def select_dropdown_option(
            self,
            index: int,
            text: str
    ) -> ToolResult:
        """
        Selects an option from a dropdown menu on a web page.

        Description:
            This tool simulates a user selecting a specific option from a dropdown menu on a webpage.
            It locates the dropdown by its index and selects the option that matches the provided visible text.
        Example:
            select_dropdown_option(index=0, text="India")
        Args:
            index (int): The index of the dropdown element on the page (e.g., 0 for the first dropdown).
            text (str): The visible text of the option to select within the dropdown.
        """
        page = await self.browser_context.get_current_page()
        selector_map = await self.browser_context.get_selector_map()
        dom_element = selector_map[index]

        # Validate that we're working with a select element
        if dom_element.tag_name != 'select':
            logger.error(
                f'Element is not a select! Tag: {dom_element.tag_name}, Attributes: {dom_element.attributes}')
            msg = f'Cannot select option: Element with index {index} is a {dom_element.tag_name}, not a select'
            return ToolResult(extracted_content=msg, include_in_memory=True)

        logger.debug(f"Attempting to select '{text}' using xpath: {dom_element.xpath}")
        logger.debug(f'Element attributes: {dom_element.attributes}')
        logger.debug(f'Element tag: {dom_element.tag_name}')

        xpath = '//' + dom_element.xpath

        try:
            frame_index = 0
            for frame in page.frames:
                try:
                    logger.debug(f'Trying frame {frame_index} URL: {frame.url}')

                    # First verify we can find the dropdown in this frame
                    find_dropdown_js = """
                                (xpath) => {
                                    try {
                                        const select = document.evaluate(xpath, document, null,
                                            XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                                        if (!select) return null;
                                        if (select.tagName.toLowerCase() !== 'select') {
                                            return {
                                                error: `Found element but it's a ${select.tagName}, not a SELECT`,
                                                found: false
                                            };
                                        }
                                        return {
                                            id: select.id,
                                            name: select.name,
                                            found: true,
                                            tagName: select.tagName,
                                            optionCount: select.options.length,
                                            currentValue: select.value,
                                            availableOptions: Array.from(select.options).map(o => o.text.trim())
                                        };
                                    } catch (e) {
                                        return {error: e.toString(), found: false};
                                    }
                                }
                            """

                    dropdown_info = await frame.evaluate(find_dropdown_js, dom_element.xpath)

                    if dropdown_info:
                        if not dropdown_info.get('found'):
                            logger.error(f'Frame {frame_index} error: {dropdown_info.get("error")}')
                            continue

                        logger.debug(f'Found dropdown in frame {frame_index}: {dropdown_info}')

                        # "label" because we are selecting by text
                        # nth(0) to disable error thrown by strict mode
                        # timeout=1000 because we are already waiting for all network events, therefore ideally we
                        # don't need to wait a lot here (default 30s)
                        selected_option_values = (
                            await frame.locator('//' + dom_element.xpath).nth(0).select_option(label=text,
                                                                                               timeout=1000)
                        )

                        msg = f'selected option {text} with value {selected_option_values}'
                        logger.info(msg + f' in frame {frame_index}')

                        return ToolResult(extracted_content=msg, include_in_memory=True)

                except Exception as frame_e:
                    logger.error(f'Frame {frame_index} attempt failed: {str(frame_e)}')
                    logger.error(f'Frame type: {type(frame)}')
                    logger.error(f'Frame URL: {frame.url}')

                frame_index += 1

            msg = f"Could not select option '{text}' in any frame"
            logger.info(msg)
            return ToolResult(extracted_content=msg, include_in_memory=True)

        except Exception as e:
            msg = f'Selection failed: {str(e)}'
            logger.error(msg)
            return ToolResult(error=msg, include_in_memory=True)
