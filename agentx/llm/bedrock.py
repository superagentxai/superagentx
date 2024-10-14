import inspect
import json
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict
import asyncio

import boto3
from openai.types import CompletionUsage
from openai.types.chat import ChatCompletion, ChatCompletionMessage, ChatCompletionMessageToolCall
from openai.types.chat.chat_completion import Choice
from pydantic import typing

from agentx.llm.client import Client
from agentx.llm.models import ChatCompletionParams, Message
from agentx.utils.helper import iter_to_aiter
from agentx.utils.helper import sync_to_async

import logging

logger = logging.getLogger(__name__)

_retries = 5


class BedrockClient(Client):

    def __init__(
            self,
            *,
            client: boto3.client
    ):
        self.client = client

    def chat_completion(
            self,
            *,
            chat_completion_params: ChatCompletionParams
    ) -> ChatCompletion | None:
        """
        Chat Completion using Bedrock-runtime in synchronous mode

        @param chat_completion_params:
        @return ChatCompletion:
        """

        if chat_completion_params:
            tools = chat_completion_params.tools

            # Get model name from client object attribute and set,
            model_id = ''.join(getattr(self.client, 'model'))

            inference_config = {}

            if chat_completion_params.temperature:
                inference_config["temperature"] = chat_completion_params.temperature

            if chat_completion_params.max_tokens:
                inference_config["maxTokens"] = chat_completion_params.max_tokens

            if chat_completion_params.top_p:
                inference_config["topP"] = chat_completion_params.top_p

            if tools:
                messages = chat_completion_params.messages
                conversations = self._construct_message(messages)

                tools_config = {"tools": tools}

                try:
                    response = self.client.converse(
                        modelId=model_id,
                        messages=conversations,
                        inferenceConfig=inference_config,
                        toolConfig=tools_config,
                    )
                except Exception as e:
                    raise RuntimeError(f"Failed to get response from Bedrock: {e}")

                if not response:
                    raise RuntimeError(f"Failed to get response from Bedrock after retrying {_retries} times.")

                try:
                    asyncio.get_running_loop()  # Triggers RuntimeError if no running event loop
                    # Create a separate thread so we can block before returning
                    with ThreadPoolExecutor(1) as pool:
                        chat_completion: ChatCompletion = pool.submit(
                            lambda: asyncio.run(
                                self.__prepare_bedrock_formatted_output_(
                                    response=response,
                                    model_id=model_id,
                                    is_async=True
                                )
                            )).result()
                        return chat_completion
                except RuntimeError as error:
                    logger.error(f'Unable tp process the result from Bedrock response {error} ')

    async def achat_completion(
            self,
            *,
            chat_completion_params: ChatCompletionParams
    ) -> ChatCompletion | None:
        """
        Chat Completion using Bedrock-runtime in asynchronous mode

        @param chat_completion_params:
        @return ChatCompletion:
        """
        if chat_completion_params:
            tools = chat_completion_params.tools

            # Get model name from client object attribute and set,
            model_id = ''.join(getattr(self.client, 'model'))

            inference_config = {}

            if chat_completion_params.temperature:
                inference_config["temperature"] = chat_completion_params.temperature

            if chat_completion_params.max_tokens:
                inference_config["maxTokens"] = chat_completion_params.max_tokens

            if chat_completion_params.top_p:
                inference_config["topP"] = chat_completion_params.top_p

            if tools:
                messages = chat_completion_params.messages
                conversations = await sync_to_async(
                    self._construct_message,
                    messages
                )

                tools_config = {"tools": tools}

                try:
                    # Convert from synchronous to asynchronous mode and invoke Bedrock client!
                    response = await sync_to_async(
                        self.client.converse,
                        modelId=model_id,
                        messages=conversations,
                        inferenceConfig=inference_config,
                        toolConfig=tools_config,
                    )
                except Exception as e:
                    raise RuntimeError(f"Failed to get response from Bedrock: {e}")

                if response is None:
                    raise RuntimeError(f"Failed to get response from Bedrock after retrying {_retries} times.")

                chat_completion: ChatCompletion = await self.__prepare_bedrock_formatted_output_(
                    response=response,
                    model_id=model_id,
                    is_async=True
                )
                return chat_completion

    @staticmethod
    async def __prepare_bedrock_formatted_output_(
            response,
            model_id: str,
            is_async: bool
    ) -> ChatCompletion:
        response_message = response["output"]["message"]

        finish_reason = (
            await sync_to_async(
                BedrockClient.convert_stop_to_finish_reason,
                response["stopReason"]
            )
            if is_async
            else await sync_to_async(
                BedrockClient.convert_stop_to_finish_reason,
                response["stopReason"]
            )
        )

        if finish_reason == "tool_calls":
            tool_calls = (
                await sync_to_async(
                    BedrockClient.convert_tool_response_to_openai_format,
                    response_message["content"]
                )
                if is_async
                else await sync_to_async(
                    BedrockClient.convert_tool_response_to_openai_format,
                    response_message["content"]
                )
            )
        else:
            tool_calls = None

        text = ""
        async for content in iter_to_aiter(response_message["content"]):
            if "text" in content:
                text = content["text"]
            # TODO: Images / Videos type need to add in future!!

        message = ChatCompletionMessage(
            role="assistant",
            content=text,
            tool_calls=tool_calls
        )

        response_usage = response["usage"]

        usage = CompletionUsage(
            prompt_tokens=response_usage["inputTokens"],
            completion_tokens=response_usage["outputTokens"],
            total_tokens=response_usage["totalTokens"],
        )

        return ChatCompletion(
            id=response["ResponseMetadata"]["RequestId"],
            choices=
            [
                Choice(
                    finish_reason=finish_reason,
                    index=0,
                    message=message
                )
            ],
            created=int(time.time()),
            model=model_id,
            object="chat.completion",
            usage=usage,
        )

    async def get_tool_json(
            self,
            *,
            func: typing.Callable
    ) -> dict:
        _func_name = func.__name__
        _doc_str = inspect.getdoc(func)
        _properties = {}
        _type_hints = typing.get_type_hints(func)
        async for param, param_type in iter_to_aiter(_type_hints.items()):
            if param != 'return':
                _properties[param] = {
                    "type": param_type.__name__,
                    "description": f"The {param.replace('_', ' ')}."
                }
        return {
            'toolSpec': {
                'name': _func_name,
                'description': _doc_str,
                "inputSchema": {
                    'json': {
                        "type": "object",
                        "properties": _properties,
                        "required": list(_properties.keys()),
                    }
                }

            }
        }

    @staticmethod
    def convert_tool_response_to_openai_format(content) -> list:

        """Converts Converse API response tool calls to AutoGen format"""
        tool_calls = []
        for tool_request in content:
            if "toolUse" in tool_request:
                tool = tool_request["toolUse"]

                tool_calls.append(
                    ChatCompletionMessageToolCall(
                        id=tool["toolUseId"],
                        function={
                            "name": tool["name"],
                            "arguments": json.dumps(tool["input"]),
                        },
                        type="function",
                    )
                )
        return tool_calls

    @staticmethod
    def convert_stop_to_finish_reason(stop_reason: str) -> str | None:
        """
        Maps Bedrock stop reasons to corresponding OpenAI finish reasons:

        - stop: when the model reaches a natural end or encounters a stop sequence,
        - length: when the maximum token limit is reached,
        - content_filter: when content is excluded due to content filtering,
        - tool_calls: when the model invokes a tool.
    """
        finish_reason_mapping = {
            "tool_use": "tool_calls",
            "finished": "stop",
            "end_turn": "stop",
            "max_tokens": "length",
            "stop_sequence": "stop",
            "complete": "stop",
            "content_filtered": "content_filter",
        }

        if stop_reason:
            return finish_reason_mapping.get(stop_reason.lower(), stop_reason.lower())

        logger.warning(f"Stop reason: {stop_reason}", UserWarning)
        return None

    @staticmethod
    def _construct_message(messages: [Message]) -> List:
        """
          Converts a list of messages into the necessary prompt format for the model.

          Args:
                messages ([Message]): A list of Message where each message contains 'role' and 'content' keys.
          Returns:
                List: List of messages in the format of bedrock runtime!
        """
        formatted_messages = []
        message = {}
        for conversation in messages:
            role = conversation.role
            if role == 'user':
                message['role'] = 'user'
                message['content'] = [{'text': conversation.content}]
            else:
                message['role'] = role
                message['content'] = conversation.content
            formatted_messages.append(message)
        return formatted_messages

    @staticmethod
    async def _format_messages(messages: List[Dict[str, str]]) -> str:
        """
        Converts a list of messages into the necessary prompt format for the model.

        Args:
            messages (List[Dict[str, str]]): A list of dictionaries where each dictionary represents a message.
                                            Each dictionary contains 'role' and 'content' keys.

        Returns:
            str: A formatted string combining all messages, structured with roles capitalized and separated by newlines.
        """
        formatted_messages = []
        async for message in iter_to_aiter(messages):
            role = message["role"].capitalize()
            content = message["content"]
            formatted_messages.append(f"\n\n{role}: {content}")

        return "".join(formatted_messages) + "\n\nAssistant:"

    def embed(self, text: str, **kwargs):
        pass

    async def aembed(self, text: str, **kwargs):
        pass
