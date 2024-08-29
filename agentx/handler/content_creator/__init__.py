from enum import Enum
from typing import Any

from langchain_core.language_models.chat_models import BaseLanguageModel
from langchain_openai.chat_models import ChatOpenAI

from agentx.exceptions import InvalidType
from agentx.handler.base import BaseHandler


class ContentCreatorType(str, Enum):
    TEXT = "TEXT"
    VIDEO = "VIDEO"
    IMAGE = "IMAGE"


class ContentCreatorHandler(BaseHandler):

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
        match action:
            case ContentCreatorType.TEXT:
                result = self.text_creation()
                return result
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
