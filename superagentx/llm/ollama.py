import inspect
import json
import logging
import re
import time
import uuid

from ollama import AsyncClient
from ollama import Client as OllamaCli
from openai.types import CompletionUsage
from openai.types.chat import ChatCompletion, ChatCompletionMessage, ChatCompletionMessageToolCall
from openai.types.chat.chat_completion import Choice
from pydantic import typing

from superagentx.llm import ChatCompletionParams
from superagentx.llm.client import Client
from superagentx.utils.helper import iter_to_aiter, ptype_to_json_scheme, sync_to_async

_retries = 5

logger = logging.getLogger(__name__)


class OllamaClient(Client):

    def __init__(
            self,
            *,
            client: AsyncClient | OllamaCli,
            **kwargs
    ):
        super().__init__(**kwargs)
        self.client = client
        self.kwargs = kwargs

    def chat_completion(
            self,
            *,
            chat_completion_params: ChatCompletionParams
    ):
        """
        Chat Completion using Ollama-runtime in synchronous mode
        @param chat_completion_params:
        @return ChatCompletion:
        """
        if chat_completion_params:
            tools = chat_completion_params.tools
            options = {}
            if chat_completion_params.top_p:
                options["top_p"] = chat_completion_params.top_p
            if chat_completion_params.temperature:
                options["temperature"] = chat_completion_params.temperature
            messages = chat_completion_params.model_dump()
            try:
                if tools:
                    response = self.client.chat(
                        model=self._model,
                        messages=messages.get("messages", []),
                        tools=tools,
                        options=options,
                        format='json'
                    )
                else:
                    response = self.client.chat(
                        model=self._model,
                        messages=messages.get("messages", []),
                        options=options,
                        format='json'
                    )
            except Exception as e:
                raise RuntimeError(f"Failed to get response from Ollama: {e}")

            if not response:
                raise RuntimeError(f"Failed to get response from Ollama after retrying {_retries} times.")

            chat_completion: ChatCompletion = self.__prepare_ollama_formatted_output(
                response=response,
                model=self._model
            )
            return chat_completion
        return None

    async def achat_completion(
            self,
            *,
            chat_completion_params: ChatCompletionParams
    ) -> ChatCompletion | None:
        """
        Chat Completion using Ollama-runtime in asynchronous mode
        @param chat_completion_params:
        @return ChatCompletion:
        """
        if chat_completion_params:
            options = {}
            tools = chat_completion_params.tools
            if chat_completion_params.top_p:
                options["top_p"] = chat_completion_params.top_p
            if chat_completion_params.temperature:
                options["temperature"] = chat_completion_params.temperature
            messages = chat_completion_params.model_dump()
            try:
                if tools:
                    response = await self.client.chat(
                        model=self._model,
                        messages=messages.get("messages", []),
                        tools=tools,
                        options=options,
                        format='json'

                    )
                else:
                    response = await self.client.chat(
                        model=self._model,
                        messages=messages.get("messages", []),
                        options=options,
                        format='json'
                    )
            except Exception as e:
                raise RuntimeError(f"Failed to get response from Ollama: {e}")

            if response is None:
                raise RuntimeError(f"Failed to get response from Ollama after retrying {_retries} times.")

            chat_completion: ChatCompletion = await sync_to_async(
                self.__prepare_ollama_formatted_output,
                response=response,
                model=self._model
            )
            return chat_completion
        return None

    @staticmethod
    def convert_tool_response_to_openai_format(content) -> list:
        """Converts Converse API response tool calls to AutoGen format"""
        tool_calls = []
        for tool_request in content:
            tool = tool_request["function"]
            tool_calls.append(
                ChatCompletionMessageToolCall(
                    id=uuid.uuid4().hex,
                    function={
                        "name": tool["name"],
                        "arguments": json.dumps(tool["arguments"]),
                    },
                    type="function",
                )
            )
        return tool_calls

    @staticmethod
    def __prepare_json_formatted(content: str):
        start = '```json\n'
        end = '```'
        if '```json' in content:
            trim_res = re.findall(
                re.escape(start) + "(.+?)" + re.escape(end),
                content,
                re.DOTALL
            )
            if trim_res:
                return trim_res[0]
            else:
                return content
        else:
            return content

    def __prepare_ollama_formatted_output(
            self,
            response,
            model: str
    ):
        logging.info(f"Response: {response}")
        response_message = response.get("message", {}).get("content", "")
        if response_message:
            response_message = self.__prepare_json_formatted(response_message)
        finish_reason = "stop"
        tool_calls = None
        if not response_message:
            tool_calls = response.get("message", {}).get("tool_calls", None)
            if tool_calls:
                tool_calls = OllamaClient.convert_tool_response_to_openai_format(
                    response.get("message", {}).get("tool_calls", None)
                )
                finish_reason = "tool_calls"
        message = ChatCompletionMessage(
            role="assistant",
            content=response_message,
            tool_calls=tool_calls
        )
        usage = CompletionUsage(
            prompt_tokens=0,
            total_tokens=0,
            completion_tokens=0,
        )
        if response.get("prompt_eval_count", None) and response.get("eval_count", None):
            total_tokens = response.get("prompt_eval_count") + response.get("eval_count")
            usage.prompt_tokens = response.get("prompt_eval_count")
            usage.completion_tokens = response.get("eval_count")
            usage.total_tokens = total_tokens

        return ChatCompletion(
            id=uuid.uuid4().hex,
            choices=
            [
                Choice(
                    finish_reason=finish_reason,
                    index=0,
                    message=message
                )
            ],
            created=int(time.time()),
            model=model,
            object="chat.completion",
            usage=usage
        )

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
            'type': 'function',
            'function': {
                'name': _func_name,
                'description': _doc_str,
                'parameters': {
                    "type": "object",
                    "properties": _properties,
                    "required": list(_properties.keys()),
                }
            }
        }

    def embed(
            self,
            text: str,
            **kwargs
    ):
        """
        Get the embedding for the given text using AsyncClient
        Args:
            text (str): The text to embed.
        Returns:
            list: The embedding vector.
        """
        text = text.replace("\n", " ")
        response = self.client.embeddings(model=self._embed_model, prompt=text)
        if response and response["embedding"]:
            return response["embedding"]
        return None

    async def aembed(
            self,
            text: str,
            **kwargs
    ):
        """
        Get the embedding for the given text using AsyncClient
        Args:
            text (str): The text to embed.
        Returns:
            list: The embedding vector.
        """
        text = text.replace("\n", " ")
        response = await self.client.embeddings(model=self._embed_model, prompt=text)
        if response and response["embedding"]:
            return response["embedding"]
        return None

    def __replace_instance_values(self, source_instance: ChatCompletionParams) -> ChatCompletionParams:
        params = self.kwargs.keys()
        for _key in params:
            if _key in source_instance.__fields__:
                setattr(source_instance, _key, self.kwargs[_key])
        return source_instance
