from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel

from superagentx.computer_use.browser.dom.history_tree_processor.tree_processor_service import DOMHistoryElement
from superagentx.computer_use.browser.dom.views import DOMState


class TabInfo(BaseModel):
    page_id: int
    url: str
    title: str


@dataclass
class BrowserState(DOMState):
    url: str
    title: str
    tabs: list[TabInfo]
    screenshot: str | None = None
    pixels_above: int = 0
    pixels_below: int = 0
    browser_errors: list[str] = field(default_factory=list)


@dataclass
class BrowserStateHistory:
    url: str
    title: str
    tabs: list[TabInfo]
    interacted_element: list[DOMHistoryElement | None]
    screenshot: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "tabs": [tab.model_dump() for tab in self.tabs],
            "screenshot": self.screenshot,
            "interacted_element": [
                el.to_dict() if el else None for el in self.interacted_element
            ],
            "url": self.url,
            "title": self.title,
        }


class BrowserError(Exception):
    """Base class for all browser errors"""


class URLNotAllowedError(BrowserError):
    """Error raised when a URL is not allowed"""