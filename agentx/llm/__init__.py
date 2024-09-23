import logging
import os
import json

from typing import List

from openai import OpenAI, AzureOpenAI, AsyncOpenAI, AsyncAzureOpenAI
from openai.types.chat import ChatCompletion

from agentx.exceptions import InvalidType
from agentx.llm.models import ChatCompletionParams
from agentx.llm.openai import OpenAIClient
from agentx.llm.types.base import LLMModelConfig
from agentx.llm.types.response import Message, Tool
from agentx.utils.llm_config import LLMType


logger = logging.getLogger(__name__)


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
            llm_config: dict
    ):
        self.llm_config_model = LLMModelConfig(**llm_config)
        llm_type = self.llm_config_model.llm_type

        match llm_type:

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
                self.client = OpenAIClient(cli)

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
                self.client = OpenAIClient(cli)

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

    async def afunc_chat_completion(
            self,
            *,
            chat_completion_params: ChatCompletionParams
    ) -> List[Message]:
        response: ChatCompletion = await self.client.achat_completion(chat_completion_params=chat_completion_params)

        # List to store multiple Message instances
        message_instances = []

        if response:
            # Iterate over each choice and create a Message instance
            for choice in response.choices:
                tool_calls_data = []
                if choice.message.tool_calls:
                    tool_calls_data = [
                        Tool(
                            tool_type=tool_call.type,
                            name=tool_call.function.name,
                            arguments=json.loads(tool_call.function.arguments)  # Use json.loads for safer parsing
                        ) for tool_call in choice.message.tool_calls
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
                        reasoning_tokens=usage_data.completion_tokens_details.get('reasoning_tokens'),
                        created=response.created
                    )
                )

        return message_instances
