import json
import logging
import os
import typing
from typing import List

import boto3
from botocore.config import Config
from openai import OpenAI, AzureOpenAI, AsyncOpenAI, AsyncAzureOpenAI
from openai.types.chat import ChatCompletion

from agentx.exceptions import InvalidType
from agentx.llm.bedrock import BedrockClient
from agentx.llm.models import ChatCompletionParams
from agentx.llm.openai import OpenAIClient
from agentx.llm.types.base import LLMModelConfig
from agentx.llm.types.response import Message, Tool
from agentx.utils.helper import iter_to_aiter
from agentx.utils.llm_config import LLMType

logger = logging.getLogger(__name__)

_retries = 5


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
        self.llm_config_model = LLMModelConfig(**llm_config)

        match self.llm_config_model.llm_type:

            case LLMType.OPENAI_CLIENT:  # OPEN AI Client Type

                # Set the API Key from pydantic model class or from environment variables.
                api_key = (
                    self.llm_config_model.api_key
                    if self.llm_config_model.api_key else os.getenv("OPENAI_API_KEY")
                )

                # Determine the client class based on async_mode
                client_class = AsyncOpenAI if self.llm_config_model.async_mode else OpenAI

                # Initialize the client with the API key
                cli = client_class(api_key=api_key)

                # Set the model attribute
                cli.model = self.llm_config_model.model

                # Assign the client to self.client
                self.client = OpenAIClient(client=cli)

            case LLMType.AZURE_OPENAI_CLIENT:

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
                    azure_deployment=azure_deployment,
                    api_version=api_version
                )

                # Set the model attribute
                cli.model = self.llm_config_model.model

                # Assign the client to self.client
                self.client = OpenAIClient(client=cli)

            case LLMType.BEDROCK_CLIENT:

                aws_region = kwargs.get("aws_region", None) or os.getenv("AWS_REGION")

                if aws_region is None:
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

                # Set the model attribute
                aws_cli.model = self.llm_config_model.model

                self.client = BedrockClient(client=aws_cli)

            case _:
                raise InvalidType(f'Not a valid LLM model `{self.llm_config_model.llm_type}`.')

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
