import logging

from anthropic import Anthropic, AsyncAnthropic
from pydantic import typing

from superagentx.llm.client import Client

logger = logging.getLogger(__name__)


class AnthropicClient(Client):

    def __init__(
            self,
            *,
            client: Anthropic | AsyncAnthropic,
            **kwargs
    ):
        super().__init__(**kwargs)
        self.client = client

    def chat_completion(self, *args, **kwargs):
        pass

    async def achat_completion(self, *args, **kwargs):
        pass

    async def get_tool_json(self, func: typing.Callable) -> dict:
        pass

    def embed(self, text: str, **kwargs):
        pass

    async def aembed(self, text: str, **kwargs):
        pass