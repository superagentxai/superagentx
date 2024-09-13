import os

from openai import AsyncOpenAI, OpenAI, AsyncAzureOpenAI, AzureOpenAI

from agentx.embeddings.types.base import EmbeddingConfig
from agentx.exceptions import InvalidType
from agentx.utils.embed_config import EmbedType
from agentx.embeddings.openai import OpenAIEmbedding


class Embeddings:

    """Model Types: openai, azure-openai, ollama, huggingface
       Open AI:

       embed_config = {
        "model": "text-embedding-ada-002",
        "api_type": "openai",
      }

    """

    def __init__(
            self,
            embed_config: dict
    ):
        self.embed_config = EmbeddingConfig(**embed_config)
        embed_type = self.embed_config.embed_type

        match embed_type:

            case EmbedType.OPENAI_CLIENT:   # Open AI Client type
                # Set the API Key from pydantic model class or from environment variables.
                api_key = (
                    self.embed_config.api_key
                    if self.embed_config.api_key else os.getenv("OPENAI_API_KEY")
                )

                # Determine the client class based on async_mode
                client_class = AsyncOpenAI if self.embed_config.async_mode else OpenAI

                # Initialize the client with the API key
                cli = client_class(api_key=api_key)

                # Set the model attribute
                cli.model = self.embed_config.model

                # Assign the client to self.client
                self.client = OpenAIEmbedding(cli)
            case EmbedType.AZURE_OPENAI_CLIENT:

                # Set the parameters from pydantic model class or from environment variables.
                api_key = self.embed_config.api_key or os.getenv("AZURE_OPENAI_API_KEY")
                base_url = self.embed_config.base_url or os.getenv("AZURE_ENDPOINT")
                azure_deployment = self.embed_config.model or os.getenv("AZURE_DEPLOYMENT")
                api_version = self.embed_config.api_version or os.getenv("API_VERSION")

                # Determine the client class based on async_mode
                client_class = AsyncAzureOpenAI if self.embed_config.async_mode else AzureOpenAI

                # Initialize the client with the gathered configuration
                cli = client_class(
                    api_key=api_key,
                    azure_endpoint=base_url,
                    azure_deployment=azure_deployment,
                    api_version=api_version
                )

                # Set the model attribute
                cli.model = self.embed_config.model

                # Assign the client to self.client
                self.client = OpenAIEmbedding(cli)
            case _:
                raise InvalidType(f'Not a valid Embedding model `{self.embed_config.embed_type}`.')

    def embed(
            self,
            **kwargs
    ):
        return self.client.embed(**kwargs)
