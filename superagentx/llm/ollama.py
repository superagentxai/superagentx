import inspect
import json
import logging
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
            client: AsyncClient | OllamaCli
    ):
        self.client = client
        self._model = getattr(self.client, 'model')
        self._embed_model = getattr(self.client, 'embed_model')

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
            model = ''.join(getattr(self.client, 'model'))
            options = {}
            if chat_completion_params.top_p:
                options["top_p"] = chat_completion_params.top_p
            if chat_completion_params.temperature:
                options["temperature"] = chat_completion_params.temperature
            messages = [message.dict() for message in chat_completion_params.messages]
            try:
                if tools:
                    response = self.client.chat(
                        model=self._model,
                        messages=messages,
                        tools=tools
                    )
                else:
                    response = self.client.chat(
                        model=self._model,
                        messages=messages
                    )
            except Exception as e:
                raise RuntimeError(f"Failed to get response from Ollama: {e}")

            if response is None:
                raise RuntimeError(f"Failed to get response from Ollama after retrying {_retries} times.")

            chat_completion: ChatCompletion = self.__prepare_ollama_formatted_output(
                response=response,
                model=model
            )
            return chat_completion

    async def achat_completion(
            self,
            *,
            chat_completion_params: ChatCompletionParams
    ) -> ChatCompletion:
        """
        Chat Completion using Ollama-runtime in asynchronous mode

        @param chat_completion_params:
        @return ChatCompletion:
        """
        if chat_completion_params:
            tools = chat_completion_params.tools
            model = ''.join(getattr(self.client, 'model'))
            options = {}
            if chat_completion_params.top_p:
                options["top_p"] = chat_completion_params.top_p
            if chat_completion_params.temperature:
                options["temperature"] = chat_completion_params.temperature
            messages = [message.dict() async for message in iter_to_aiter(chat_completion_params.messages)]
            try:
                if tools:
                    response = await self.client.chat(
                        model=self._model,
                        messages=messages,
                        tools=tools

                    )
                else:
                    response = await self.client.chat(
                        model=self._model,
                        messages=messages
                    )
            except Exception as e:
                raise RuntimeError(f"Failed to get response from Ollama: {e}")

            if response is None:
                raise RuntimeError(f"Failed to get response from Ollama after retrying {_retries} times.")

            chat_completion: ChatCompletion = await sync_to_async(
                self.__prepare_ollama_formatted_output,
                response=response,
                model=model
            )
            return chat_completion

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
    def __prepare_ollama_formatted_output(
            response,
            model: str
    ):
        logging.info(f"Response: {response}")
        response_message = response["message"]["content"]
        finish_reason = "stop"
        tool_calls = None
        if not response_message:
            message_keys = response["message"].keys()
            if "tool_calls" in message_keys:
                tool_calls = OllamaClient.convert_tool_response_to_openai_format(
                    response["message"]["tool_calls"]
                )
                finish_reason = "tool_calls"
        message = ChatCompletionMessage(
            role="assistant",
            content=response_message,
            tool_calls=tool_calls
        )
        total_tokens = response["prompt_eval_count"] + response["eval_count"]
        usage = CompletionUsage(
            prompt_tokens=response["prompt_eval_count"],
            completion_tokens=response["eval_count"],
            total_tokens=total_tokens,
        )

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

    async def get_tool_json(
            self,
            func: typing.Callable
    ) -> dict:
        _func_name = func.__name__
        _doc_str = inspect.getdoc(func)
        _properties = {}
        _type_hints = typing.get_type_hints(func)
        async for param, param_type in iter_to_aiter(_type_hints.items()):
            if param != 'return':
                _properties[param] = {
                    "type": await ptype_to_json_scheme(param_type.__name__),
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
            return [response["embedding"]]

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
            return [response["embedding"]]
