import pytest

from superagentx.computer_use.browser.browser import Browser, BrowserConfig


@pytest.mark.asyncio
async def test_highlight_elements():
    browser = Browser(config=BrowserConfig(headless=False, disable_security=True, browser_type='firefox'))

    async with await browser.new_context() as context:
        page = await context.get_current_page()
        await page.goto('https://dictionary.cambridge.org')

        state = await context.get_state()
        print(f"Browser State : {state}")
