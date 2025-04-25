import asyncio
import gc
import logging
import subprocess
from typing import List, Optional

from pydantic import BaseModel, Field
from playwright._impl._api_structures import ProxySettings
from playwright.async_api import Browser as PlaywrightBrowser
from playwright.async_api import (
    Playwright,
    async_playwright,
)
from superagentx.computer_use.utils import BROWSER_SECURITY_ARGS, HEADLESS_ARGS

from superagentx.computer_use.browser.context import BrowserContext, BrowserContextConfig

logger = logging.getLogger(__name__)


class BrowserConfig(BaseModel):
    headless: bool = False
    disable_security: bool = True
    extra_chromium_args: List[str] = Field(default_factory=list)
    chrome_instance_path: Optional[str] = None
    wss_url: Optional[str] = None
    cdp_url: Optional[str] = None
    proxy: Optional[ProxySettings] = None
    new_context_config: BrowserContextConfig = Field(default_factory=BrowserContextConfig)
    _force_keep_browser_alive: bool = False


class Browser:

    def __init__(self, config: BrowserConfig = BrowserConfig()):
        self.config = config
        self.playwright: Optional[Playwright] = None
        self.playwright_browser: Optional[PlaywrightBrowser] = None

        self.disable_security_args = []
        if self.config.disable_security:
            self.disable_security_args = BROWSER_SECURITY_ARGS

    async def _init(self):
        """Initialize the browser session"""
        self.playwright = await async_playwright().start()
        self.playwright_browser = await self._setup_browser(self.playwright)
        return self.playwright_browser

    async def new_context(self, config: BrowserContextConfig = BrowserContextConfig()) -> BrowserContext:
        """Create a browser context"""
        return BrowserContext(config=config, browser=self)

    async def get_playwright_browser(self) -> PlaywrightBrowser:
        """Get a browser instance"""
        if self.playwright_browser is None:
            return await self._init()
        return self.playwright_browser

    async def _setup_cdp(self, playwright: Playwright) -> PlaywrightBrowser:
        if not self.config.cdp_url:
            raise ValueError('CDP URL is required')
        logger.info(f'Connecting to remote browser via CDP {self.config.cdp_url}')
        return await playwright.chromium.connect_over_cdp(self.config.cdp_url)

    async def _setup_wss(self, playwright: Playwright) -> PlaywrightBrowser:
        if not self.config.wss_url:
            raise ValueError('WSS URL is required')
        logger.info(f'Connecting to remote browser via WSS {self.config.wss_url}')
        return await playwright.chromium.connect(self.config.wss_url)

    async def _setup_browser_with_instance(self, playwright: Playwright) -> PlaywrightBrowser:
        if not self.config.chrome_instance_path:
            raise ValueError('Chrome instance path is required')

        import requests

        try:
            response = requests.get('http://localhost:9222/json/version', timeout=2)
            if response.status_code == 200:
                logger.info('Reusing existing Chrome instance')
                return await playwright.chromium.connect_over_cdp(
                    endpoint_url='http://localhost:9222',
                    timeout=20000,
                )
        except requests.ConnectionError:
            logger.debug('No existing Chrome instance found, starting a new one')

        subprocess.Popen(
            [
                self.config.chrome_instance_path,
                '--remote-debugging-port=9222',
            ] + self.config.extra_chromium_args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        for _ in range(10):
            try:
                response = requests.get('http://localhost:9222/json/version', timeout=2)
                if response.status_code == 200:
                    break
            except requests.ConnectionError:
                pass
            await asyncio.sleep(1)

        try:
            return await playwright.chromium.connect_over_cdp(
                endpoint_url='http://localhost:9222',
                timeout=20000,
            )
        except Exception as e:
            logger.error(f'Failed to start a new Chrome instance: {str(e)}')
            raise RuntimeError(
                'To start Chrome in debug mode, close all existing Chrome instances and try again.'
            )

    async def _setup_standard_browser(self, playwright: Playwright) -> PlaywrightBrowser:
        return await playwright.chromium.launch(
            headless=self.config.headless,
            args=HEADLESS_ARGS + self.disable_security_args + self.config.extra_chromium_args,
            proxy=self.config.proxy,
        )

    async def _setup_browser(self, playwright: Playwright) -> PlaywrightBrowser:
        try:
            if self.config.cdp_url:
                return await self._setup_cdp(playwright)
            if self.config.wss_url:
                return await self._setup_wss(playwright)
            if self.config.chrome_instance_path:
                return await self._setup_browser_with_instance(playwright)
            return await self._setup_standard_browser(playwright)
        except Exception as e:
            logger.error(f'Failed to initialize Playwright browser: {str(e)}')
            raise

    async def close(self):
        """Close the browser instance"""
        try:
            if not self.config._force_keep_browser_alive:
                if self.playwright_browser:
                    await self.playwright_browser.close()
                    del self.playwright_browser
                if self.playwright:
                    await self.playwright.stop()
                    del self.playwright
        except Exception as e:
            logger.debug(f'Failed to close browser properly: {e}')
        finally:
            self.playwright_browser = None
            self.playwright = None
            gc.collect()

    def __del__(self):
        try:
            if self.playwright_browser or self.playwright:
                loop = asyncio.get_running_loop()
                if loop.is_running():
                    loop.create_task(self.close())
                else:
                    asyncio.run(self.close())
        except Exception as e:
            logger.debug(f'Failed to cleanup browser in destructor: {e}')
