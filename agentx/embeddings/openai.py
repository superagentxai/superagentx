import logging
import re

from openai import OpenAI, AzureOpenAI, AsyncOpenAI, AsyncAzureOpenAI

from agentx.embeddings.base import BaseEmbeddings

logger = logging.getLogger(__name__)
_OPEN_API_BASE_URL_PREFIX = "https://api.openai.com"


class OpenAIEmbedding(BaseEmbeddings):

    def __init__(
            self,
            client: OpenAI | AsyncOpenAI | AzureOpenAI | AsyncAzureOpenAI
    ):
        self.client = client

        self.client.model = self.client.model or "text-embedding-3-small"

        if (
                not isinstance(self.client, OpenAI | AsyncOpenAI | AzureOpenAI | AsyncAzureOpenAI)
                and not str(client.base_url).startswith(_OPEN_API_BASE_URL_PREFIX)
                and not OpenAIEmbedding.is_valid_api_key(self.client.api_key)
        ):
            logger.info(
                "OpenAI or Azure hosted Open AI client, is not valid!"
            )
            super().__init__()

    def embed(self, text: str, **kwargs):
        """
        Get the embedding for the given text using OpenAI.

        Args:
            text (str): The text to embed.

        Returns:
            list: The embedding vector.
        """
        text = text.replace("\n", " ")
        model = getattr(self.client, 'model')
        return (
            self.client.embeddings.create(
                input=[text],
                model=model,
                **kwargs
            )
            .data[0]
            .embedding
        )

    async def aembed(self, text: str, **kwargs):
        """
        Get the embedding for the given text using OpenAI.

        Args:
            text (str): The text to embed.

        Returns:
            list: The embedding vector.
        """
        text = text.replace("\n", " ")
        model = getattr(self.client, 'model')
        response = await self.client.embeddings.create(
            input=[text],
            model=model,
        )
        return response.data[0].embedding

    @staticmethod
    def is_valid_api_key(api_key: str) -> bool:
        """Determine if input is valid OpenAI API key.

        Args:
            api_key (str): An input string to be validated.

        Returns:
            bool: A boolean that indicates if input is valid OpenAI API key.
        """
        api_key_re = re.compile(r"^sk-([A-Za-z0-9]+(-+[A-Za-z0-9]+)*-)?[A-Za-z0-9]{32,}$")
        return bool(re.fullmatch(api_key_re, api_key))
