import asyncio
import aiohttp
import gc
import logging
from playwright._impl._api_structures import ProxySettings
from playwright.async_api import Browser as PlaywrightBrowser
from playwright.async_api import (
    Playwright,
    async_playwright,
)
from dataclasses import dataclass, field
from superagentx.computer_use.constants import BROWSER_SECURITY_ARGS, HEADLESS_ARGS

from superagentx.computer_use.browser.context import BrowserContext, BrowserContextConfig

logger = logging.getLogger(__name__)


@dataclass
class BrowserConfig:
    headless: bool = False
    disable_security: bool = True
    extra_chromium_args: list[str] = field(default_factory=list)
    chrome_instance_path: str | None = None
    wss_url: str | None = None
    cdp_url: str | None = None
    proxy: ProxySettings | None = None
    new_context_config: BrowserContextConfig = field(default_factory=BrowserContextConfig)
    _force_keep_browser_alive: bool = False
    browser_type: str = "chromium"  # Options: "chromium", "firefox", "webkit"


class Browser:

    def __init__(self, config: BrowserConfig = BrowserConfig()):
        self.config = config
        self.playwright: Playwright | None = None
        self.playwright_browser: Playwright | None = None

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

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=2)) as session:
                async with session.get('http://localhost:9222/json/version') as response:
                    if response.status == 200:
                        logger.info('Reusing existing Chrome instance')
                        return await playwright.chromium.connect_over_cdp(
                            endpoint_url='http://localhost:9222',
                            timeout=20000,
                        )
        except aiohttp.ClientConnectorError:
            logger.debug('No existing Chrome instance found, starting a new one')

        process = await asyncio.create_subprocess_exec(
            self.config.chrome_instance_path,
            '--remote-debugging-port=9222',
            *self.config.extra_chromium_args,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )

        for _ in range(10):
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=2)) as session:
                    async with session.get('http://localhost:9222/json/version') as response:
                        if response.status == 200:
                            break
            except aiohttp.ClientConnectorError:
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
        browser_launcher = getattr(playwright, self.config.browser_type, None)
        if not browser_launcher:
            raise ValueError(f"Unsupported browser type: {self.config.browser_type}")

        args = HEADLESS_ARGS + self.disable_security_args + self.config.extra_chromium_args \
            if self.config.browser_type == "chromium" else []

        return await browser_launcher.launch(
            headless=self.config.headless,
            args=args,
            proxy=self.config.proxy,
        )

    async def _setup_browser(self, playwright: Playwright) -> PlaywrightBrowser:
        try:
            if self.config.browser_type != "chromium" and (
                    self.config.cdp_url or self.config.wss_url or self.config.chrome_instance_path):
                raise ValueError("CDP/WSS/Instance path options are only supported for Chromium.")

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
