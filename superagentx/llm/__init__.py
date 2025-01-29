import json
import logging
import os
import typing
from typing import List

import boto3
from botocore.config import Config
from ollama import AsyncClient
from openai import OpenAI, AzureOpenAI, AsyncOpenAI, AsyncAzureOpenAI
from openai.types.chat import ChatCompletion

from superagentx.exceptions import InvalidType
from superagentx.llm.bedrock import BedrockClient
from superagentx.llm.constants import DEFAULT_OPENAI_EMBED, DEFAULT_BEDROCK_EMBED, DEFAULT_OLLAMA_EMBED
from superagentx.llm.models import ChatCompletionParams
from superagentx.llm.ollama import OllamaClient
from superagentx.llm.openai import OpenAIClient
from superagentx.llm.types.base import LLMModelConfig
from superagentx.llm.types.response import Message, Tool
from superagentx.utils.helper import iter_to_aiter
from superagentx.utils.llm_config import LLMType

logger = logging.getLogger(__name__)

_retries = 5
_deepseek_base_url = 'https://api.deepseek.com'


class LLMClient:
    """Base LLM Client to create LLM client based on model llm_type.

       Model Types: openai, azure-openai, llama, gemini, mistral, bedrock, together, groq, anthropic.

       Open AI:

       llm_config = {
        "model": "gpt-4o",
        "api_type": "openai",
      }

      llm_config = {
        "model": "gpt-4o",
        "api_type": "openai",
      }

    """

    def __init__(
            self,
            *,
            llm_config: dict,
            **kwargs
    ):
        self.llm_config = llm_config
        self.llm_config_model = LLMModelConfig(**self.llm_config)

        match self.llm_config_model.llm_type:
            case LLMType.OPENAI_CLIENT | LLMType.DEEPSEEK:
                self.client = self._init_openai_cli()
                if LLMType.DEEPSEEK:
                    self.client.base_url = _deepseek_base_url
            case LLMType.AZURE_OPENAI_CLIENT:
                self.client = self._init_azure_openai_cli()
            case LLMType.BEDROCK_CLIENT:
                self.client = self._init_bedrock_cli(**kwargs)
            case LLMType.OLLAMA:
                self.client = self._init_ollama_cli(**kwargs)
            case _:
                raise InvalidType(f'Not a valid LLM model `{self.llm_config_model.llm_type}`.')

    def _init_openai_cli(self) -> OpenAIClient:
        # Set the API Key from pydantic model class or from environment variables.
        api_key = (
            self.llm_config_model.api_key
            if self.llm_config_model.api_key else os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
        )

        # Determine the client class based on async_mode
        client_class = AsyncOpenAI if self.llm_config_model.async_mode else OpenAI

        # Initialize the client with the API key
        cli = client_class(api_key=api_key, base_url=self.llm_config_model.base_url or None)

        # Set the embed model attribute
        embed_model = self.llm_config_model.embed_model

        # Assign the client to self.client
        return OpenAIClient(
            client=cli,
            model=self.llm_config_model.model,
            embed_model=DEFAULT_OPENAI_EMBED if not embed_model else embed_model
        )

    def _init_azure_openai_cli(self) -> OpenAIClient:
        # Set the parameters from pydantic model class or from environment variables.
        api_key = self.llm_config_model.api_key or os.getenv("AZURE_OPENAI_API_KEY")
        base_url = self.llm_config_model.base_url or os.getenv("AZURE_ENDPOINT")
        azure_deployment = self.llm_config_model.model or os.getenv("AZURE_DEPLOYMENT")
        api_version = self.llm_config_model.api_version or os.getenv("API_VERSION")

        # Determine the client class based on async_mode
        client_class = AsyncAzureOpenAI if self.llm_config_model.async_mode else AzureOpenAI

        # Initialize the client with the gathered configuration
        cli = client_class(
            api_key=api_key,
            azure_endpoint=base_url,
            api_version=api_version
        )

        # Assign the client to self.client
        return OpenAIClient(
            client=cli,
            model=self.llm_config_model.model,
            embed_model=self.llm_config_model.embed_model
        )

    def _init_bedrock_cli(self, **kwargs) -> BedrockClient:
        aws_region = kwargs.get("aws_region", None) or os.getenv("AWS_REGION")

        if not aws_region is None:
            raise ValueError("Region is required to use the Amazon Bedrock API.")

        aws_access_key = kwargs.get("aws_access_key", None) or os.getenv("AWS_ACCESS_KEY")
        aws_secret_key = kwargs.get("aws_secret_key", None) or os.getenv("AWS_SECRET_KEY")

        # Initialize Bedrock client, session, and runtime
        bedrock_config = Config(
            region_name=aws_region,
            signature_version="v4",
            retries={
                "max_attempts": _retries,
                "mode": "standard"
            },
        )

        # Assign Bedrock client to self.client
        aws_cli = boto3.client(
            service_name="bedrock-runtime",
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            config=bedrock_config
        )

        # Set the embed model attribute
        embed_model = self.llm_config_model.embed_model

        return BedrockClient(
            client=aws_cli,
            model=self.llm_config_model.model,
            embed_model=DEFAULT_BEDROCK_EMBED if not embed_model else embed_model
        )

    def _init_ollama_cli(self, **kwargs):
        host = kwargs.get("host", None) or os.getenv("OLLAMA_HOST")

        cli = AsyncClient(host=host)
        embed_model = self.llm_config_model.embed_model
        return OllamaClient(
            client=cli,
            embed_model=DEFAULT_OLLAMA_EMBED if not embed_model else embed_model,
            model=self.llm_config_model.model,
            **kwargs
        )

    def chat_completion(
            self,
            *,
            chat_completion_params: ChatCompletionParams
    ) -> ChatCompletion:
        return self.client.chat_completion(chat_completion_params=chat_completion_params)

    async def achat_completion(
            self,
            *,
            chat_completion_params: ChatCompletionParams
    ) -> ChatCompletion:
        return await self.client.achat_completion(chat_completion_params=chat_completion_params)

    async def get_tool_json(
            self,
            *,
            func: typing.Callable
    ) -> dict:
        return await self.client.get_tool_json(func=func)

    def embed(
            self,
            *,
            text: str,
            **kwargs
    ):
        return self.client.embed(
            text,
            **kwargs
        )

    async def aembed(
            self,
            *,
            text: str,
            **kwargs
    ):
        return await self.client.aembed(
            text,
            **kwargs
        )

    async def afunc_chat_completion(
            self,
            *,
            chat_completion_params: ChatCompletionParams
    ) -> List[Message]:

        stream = bool(chat_completion_params.stream)

        # Most models don't support streaming with tool use
        if stream:
            logger.warning(
                "Streaming is not currently supported, streaming will be disabled.",
            )
            chat_completion_params.stream = False

        response: ChatCompletion = await self.client.achat_completion(chat_completion_params=chat_completion_params)

        # List to store multiple Message instances
        message_instances = []

        if response:
            # Iterate over each choice and create a Message instance
            async for choice in iter_to_aiter(response.choices):
                tool_calls_data = []
                if choice.message.tool_calls:
                    tool_calls_data = [
                        Tool(
                            tool_type=tool_call.type,
                            name=tool_call.function.name,
                            arguments=json.loads(tool_call.function.arguments)  # Use json.loads for safer parsing
                        ) async for tool_call in iter_to_aiter(choice.message.tool_calls)
                    ]

                # Extract token details from usage
                usage_data = response.usage

                # Add the created Message instance to the list
                message_instances.append(
                    Message(
                        role=choice.message.role,
                        model=response.model,
                        content=choice.message.content,
                        tool_calls=tool_calls_data if tool_calls_data else None,
                        completion_tokens=usage_data.completion_tokens,
                        prompt_tokens=usage_data.prompt_tokens,
                        total_tokens=usage_data.total_tokens,
                        reasoning_tokens=usage_data.completion_tokens_details.reasoning_tokens if usage_data.completion_tokens_details else 0,
                        created=response.created
                    )
                )

        return message_instances
