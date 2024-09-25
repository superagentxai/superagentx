from abc import ABC

from langchain_core.language_models.chat_models import BaseLanguageModel
from langchain_openai.chat_models import ChatOpenAI

from agentx.handler.base import BaseHandler


class ContentCreatorHandler(BaseHandler, ABC):
    """
       An abstract handler class for managing content creation operations.
       This class extends BaseHandler and defines the interface for creating various types of content,
       such as text, images, and videos. Subclasses must implement specific methods for content generation and processing.
    """

    def __init__(
            self,
            prompt: str,
            llm: BaseLanguageModel
    ):
        self.prompt = prompt
        self.llm = llm


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
        # TODO: Implement later
        pass

    async def image_creation(
            self
    ):
        """
           Asynchronously generates or creates images using predefined settings or internal logic.
           This method manages the image creation process without needing external parameters.
        """
        # TODO: Implement later
        pass

    def __dir__(self):
        return (
            'text_creation'
        )
