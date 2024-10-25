from superagentx.handler.base import BaseHandler
from superagentx.handler.decorators import tool
from superagentx.llm import LLMClient
from superagentx.llm.models import ChatCompletionParams


class AIHandler(BaseHandler):
    """
       An abstract handler class for managing content creation operations.
       This class extends BaseHandler and defines the interface for creating various types of content,
       such as text, images, and videos. Subclasses must implement specific methods for content generation and processing.
    """

    def __init__(
            self,
            llm: LLMClient,
            role: str | None = None,
            story_content: str | None = None
    ):
        super().__init__()
        self.llm = llm
        self.role = role
        self.story_content = story_content

        if not self.role:
            self.role = "You are a helpful assistant."

    @tool
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
            @param instruction: A string containing the user instruction or prompt that guides the text generation process.

        """
        content = instruction
        if self.story_content:
            content = f"\nBack Story: {self.story_content} Instruction: {instruction}"
        messages = [
            {
                "role": "system",
                "content": self.role
            },
            {
                "role": "user",
                "content": content
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
