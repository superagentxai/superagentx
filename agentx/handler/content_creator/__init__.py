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

    async def handle(
            self,
            *,
            action: str | Enum,
            **kwargs
    ) -> Any:
        """
            Asynchronously handles the given action, which can be a string or an Enum, while processing additional keyword arguments.
            sExecutes the appropriate logic based on the action and provided parameters.

            parameters:
            action (str | Enum): The action to be performed. This can either be a string or an Enum value representing the action.
            **kwargs: Additional keyword arguments that may be passed to customize the behavior of the handler.

            Returns:
            Any: The result of handling the action. The return type may vary depending on the specific action handled.
        """

        if isinstance(action, str):
            action = action.lower()
        match action:
            case ContentCreatorType.TEXT:
                return await self.text_creation()
            case ContentCreatorType.IMAGE:
                raise NotImplementedError(f"{action} will be implement in future ")
            case ContentCreatorType.VIDEO:
                raise NotImplementedError(f"{action} will be implement in future ")
            case _:
                raise InvalidType(f"{action} is not supported")

    async def text_creation(
            self
    ):
        """
           Asynchronously generates or creates text based on predefined logic or input data.
           This method manages the process of text creation without requiring additional parameters.
        """

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

    async def video_creation(
            self
    ):
        """
            Asynchronously creates or generates video content based on internal logic or preset parameters.
            This method handles the video creation process without requiring external inputs.
        """

        pass

    async def image_creation(
            self
    ):
        """
           Asynchronously generates or creates images using predefined settings or internal logic.
           This method manages the image creation process without needing external parameters.
        """

        pass

    def __dir__(self):
        return (
            'text_creation',
            'video_creation',
            'image_creation'
        )

