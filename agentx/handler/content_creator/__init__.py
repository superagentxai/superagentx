from abc import ABC
from enum import Enum
from typing import Any

from langchain_core.language_models.chat_models import BaseLanguageModel
from langchain_openai.chat_models import ChatOpenAI

from agentx.exceptions import InvalidType
from agentx.handler.base import BaseHandler


class ContentCreatorType(str, Enum):
    TEXT = "text"
    VIDEO = "video"
    IMAGE = "image"


class ContentCreatorHandler(BaseHandler, ABC):

    def __init__(
            self,
            prompt: str,
            llm: BaseLanguageModel
    ):
        self.prompt = prompt
        self.llm = llm

    def handle(
            self,
            *,
            action: str | Enum,
            **kwargs
    ) -> Any:
        if isinstance(action, str):
            action = action.lower()
        match action:
            case ContentCreatorType.TEXT:
                return self.text_creation()
            case ContentCreatorType.IMAGE:
                raise NotImplementedError(f"{action} will be implement in future ")
            case ContentCreatorType.VIDEO:
                raise NotImplementedError(f"{action} will be implement in future ")
            case _:
                raise InvalidType(f"{action} is not supported")

    def text_creation(self):
        messages = self.prompt
        if isinstance(self.llm, ChatOpenAI):
            messages = [
                (
                    "human",
                    self.prompt
                )
            ]
        chain = self.llm.invoke(messages)
        return chain.content

    def video_creation(self):
        pass

    def image_creation(self):
        pass

    async def ahandle(
            self,
            *,
            action: str | Enum,
            **kwargs
    ) -> Any:
        if isinstance(action, str):
            action = action.lower()
        match action:
            case ContentCreatorType.TEXT:
                return await self.atext_creation()
            case ContentCreatorType.IMAGE:
                raise NotImplementedError(f"{action} will be implement in future ")
            case ContentCreatorType.VIDEO:
                raise NotImplementedError(f"{action} will be implement in future ")
            case _:
                raise InvalidType(f"{action} is not supported")

    async def atext_creation(self):
        messages = self.prompt
        if isinstance(self.llm, ChatOpenAI):
            messages = [
                (
                    "human",
                    self.prompt
                )
            ]
        chain = await self.llm.ainvoke(messages)
        return chain.content

    async def avideo_creation(self):
        pass

    async def aimage_creation(self):
        pass
