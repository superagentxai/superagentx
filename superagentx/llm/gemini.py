import base64
import json
import logging
import time
import uuid
from typing import Any
import inspect

from google import genai
from google.genai import types
from openai.types import CompletionUsage
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion_message_tool_call import ChatCompletionMessageToolCall, Function
from pydantic import typing

from superagentx.llm.client import Client
from superagentx.llm.models import ChatCompletionParams, Message
from superagentx.utils.helper import sync_to_async, iter_to_aiter, ptype_to_json_scheme

logger = logging.getLogger(__name__)

"""
 Gemini LLM Client API.
 Refer Doc : https://ai.google.dev/gemini-api/docs/text-generation
"""


class GeminiClient(Client):

    def __init__(
            self,
            *,
            client: genai.client,
            **kwargs
    ):
        super().__init__(**kwargs)
        self.client: genai.client = client
        self.llm_params: dict = kwargs

        self._embed_model_cli = kwargs.get("embed_model")

    def chat_completion(self, *, chat_completion_params: ChatCompletionParams) -> ChatCompletion:
        """
        Content generation model - Sync
        """
        kwargs = self._build_chat_kwargs(chat_completion_params)
        logger.debug(f"Gemini Input Structure {kwargs}")

        response: types.GenerateContentResponse = self.client.models.generate_content(**kwargs)
        chat_completion_response = self.convert_gemini_response_to_openai_chat_completion(response, self._model)

        logger.debug(f"Gemini Formatted Response : {chat_completion_response}")
        return chat_completion_response

    async def achat_completion(self, *, chat_completion_params: ChatCompletionParams) -> ChatCompletion:
        """
        Content generation model - Async
        """
        kwargs = await sync_to_async(self._build_chat_kwargs, chat_completion_params)
        logger.debug(f"Gemini Input Structure {kwargs}")

        response: types.GenerateContentResponse = await self.client.aio.models.generate_content(**kwargs)
        chat_completion_response = await sync_to_async(self.convert_gemini_response_to_openai_chat_completion, response,
                                                       self._model)

        logger.debug(f"Gemini Formatted Response : {chat_completion_response}")
        return chat_completion_response

    def _build_chat_kwargs(self, chat_completion_params: ChatCompletionParams) -> dict:
        """
        Shared method to build kwargs and inference config.
        """
        if not chat_completion_params:
            return {}

        inference_config = {}
        kwargs = {"model": self._model}

        if chat_completion_params.messages:
            user_messages, system_message = self._construct_message(contents=chat_completion_params.messages)
            logger.debug(f"User Messages : {user_messages}")
            kwargs["contents"] = user_messages

            if system_message:
                inference_config["system_instruction"] = system_message

        if chat_completion_params.tools:
            tools = types.Tool(function_declarations=chat_completion_params.tools)
            inference_config["tools"] = [tools]

        if chat_completion_params.stop:
            inference_config["stopSequences"] = chat_completion_params.stop

        if chat_completion_params.temperature:
            inference_config["temperature"] = chat_completion_params.temperature

        if chat_completion_params.max_tokens:
            inference_config["maxOutputTokens"] = chat_completion_params.max_tokens

        if chat_completion_params.top_p:
            inference_config["topP"] = chat_completion_params.top_p

        if chat_completion_params.top_k:
            inference_config["topK"] = chat_completion_params.top_k

        kwargs["config"] = types.GenerateContentConfig(**inference_config)
        return kwargs

    @staticmethod
    def _construct_message(contents: [Message]) -> tuple[list, Any | None]:
        """"
            Converts a list of messages into the necessary prompt format for the model.
        """
        formatted_user_messages: list[str] = []
        formatted_system_message: Any | None = None
        image_data: list[str] = []

        for conversation in contents:
            role = conversation.role
            content = conversation.content

            if role == 'user' or role == 'assistant':
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict):
                            # Assuming the dictionary might contain 'type', 'text', or 'image_url' keys
                            if 'image_url' in item:
                                image_data.append(str(item['image_url']))
                            elif 'text' in item:
                                formatted_user_messages.append(str(item['text']))
                            else:
                                # Handle other potential dictionary structures within the list if needed
                                for value in item.values():
                                    formatted_user_messages.append(str(value))
                        else:
                            formatted_user_messages.append(str(item))
                elif isinstance(content, dict):
                    # Assuming simple key-value pairs where values are relevant
                    for value in content.values():
                        formatted_user_messages.append(str(value))
                else:
                    formatted_user_messages.append(str(content))
            elif role == 'system':
                if not formatted_system_message and content:
                    formatted_system_message = content

        if image_data:
            return ["\n".join(formatted_user_messages), "\n\n".join(image_data)], formatted_system_message
        else:
            return formatted_user_messages, formatted_system_message

    @staticmethod
    def convert_gemini_response_to_openai_chat_completion(response: types.GenerateContentResponse,
                                                          model_id: str, ) -> ChatCompletion:
        """
        Converts Gemini response function calls to OpenAI ChatCompletion format.
        :rtype: object
        """
        if response:
            candidates = response.candidates
            usage = response.usage_metadata
            logger.debug(f"Usage Token : {response}")
            token_usage = None
            choices = []
            for idx, candidate in enumerate(candidates):
                tool_calls = []
                content = None
                for part in candidate.content.parts:
                    if part.function_call:
                        function_call = part.function_call
                        tool_calls.append(
                            ChatCompletionMessageToolCall(
                                id=str(uuid.uuid4()),  # Generate unique UUID for each tool call.
                                function=Function(
                                    name=function_call.name,
                                    arguments=json.dumps(function_call.args or {})
                                ),
                                type="function"
                            )
                        )
                    content = part.text

                msg = ChatCompletionMessage(
                    role="assistant",
                    content=content,
                    tool_calls=tool_calls if tool_calls else None
                )
                choices.append(
                    {
                        "index": idx,
                        "message": msg,
                        "finish_reason": candidate.finish_reason.lower() if candidate.finish_reason else 'stop'
                        # Maps Gemini's FinishReason.STOP.
                    }
                )

            if usage:
                token_usage = CompletionUsage(
                    prompt_tokens=usage.prompt_token_count,
                    completion_tokens=usage.candidates_token_count,
                    total_tokens=usage.total_token_count,
                )

            return ChatCompletion(
                id=f"gemini_chat-{uuid.uuid4()}",  # OpenAI-style completion ID.
                choices=choices,
                created=int(time.time()),  # Current timestamp.
                model=model_id,  # Or whichever model you want to set.
                object="chat.completion",
                usage=token_usage  # Map usage if needed.
            )

    @staticmethod
    def convert_gemini_response_to_openai_format(candidates) -> list:
        """
           Converts Gemini response function calls to OpenAI ChatCompletionMessageToolCall format.

        """
        tool_calls = []
        for candidate in candidates:

            for part in candidate.content.parts:
                if part.function_call:
                    function_call = part.function_call
                    tool_calls.append(
                        ChatCompletionMessageToolCall(
                            id="auto-generated-id",  # Gemini doesn't seem to provide ID, so generate or assign here.
                            function=Function(
                                name=function_call.name,
                                arguments=json.dumps(function_call.args or {})
                            ),
                            type="function"
                        )
                    )
        return tool_calls

    async def get_tool_json(self, func: typing.Callable) -> dict:
        _func_name = func.__name__
        _doc_str = inspect.getdoc(func)
        _properties = {}
        _type_hints = typing.get_type_hints(func)
        async for param, param_type in iter_to_aiter(_type_hints.items()):
            if param != 'return':
                _type = await ptype_to_json_scheme(param_type.__name__)
                if _type == "array":
                    if hasattr(param_type, "__args__"):
                        _properties[param] = {
                            "type": _type,
                            "description": f"The {param.replace('_', ' ')}.",
                            'items': {
                                "type": await ptype_to_json_scheme(param_type.__args__[0].__name__)
                            }
                        }
                    else:
                        _properties[param] = {
                            "type": _type,
                            "description": f"The {param.replace('_', ' ')}.",
                            'items': {
                                "type": "object"
                            }
                        }
                else:
                    _properties[param] = {
                        "type": _type,
                        "description": f"The {param.replace('_', ' ')}."
                    }

        return {
            'name': _func_name,
            'description': _doc_str,
            'parameters': {
                "type": "object",
                "properties": _properties,
            }
        }

    def embed(self, text: str, **kwargs):
        result = self.client.models.embed_content(self._embed_model_cli, text)
        return result

    async def aembed(self, text: str, **kwargs):
        result = await sync_to_async(self.client.models.embed_content, self._embed_model_cli, text)
        return result
