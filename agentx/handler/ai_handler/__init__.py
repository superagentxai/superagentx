from agentx.handler.base import BaseHandler
from agentx.llm import LLMClient
from agentx.llm.models import ChatCompletionParams


class AIHandler(BaseHandler):
    """
       An abstract handler class for managing content creation operations.
       This class extends BaseHandler and defines the interface for creating various types of content,
       such as text, images, and videos. Subclasses must implement specific methods for content generation and processing.
    """

    def __init__(
            self,
            llm: LLMClient
    ):
        self.llm = llm

    async def text_creation(
            self,
            *,
            instruction: str
    ):
        """
        Generates or creates some form of text content when called. The text being created might involve combining
        words, sentences, or paragraphs for various purposes. Since it’s part of a larger process, it could be used
        for tasks like preparing data, generating messages, or any other text-related activity.

        Args:
            instruction(str):  A string containing the instruction or prompt that guides the text generation process.

        """
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user",
                "content": instruction
            }
        ]
        chat_completion = ChatCompletionParams(
            messages=messages
        )
        return await self.llm.achat_completion(
            chat_completion_params=chat_completion
        )

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
            'text_creation',
        )
