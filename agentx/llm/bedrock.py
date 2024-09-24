import inspect
from typing import List, Dict

import boto3
from openai.types.chat import ChatCompletion
from pydantic import typing

from agentx.llm.client import Client
from agentx.llm.models import ChatCompletionParams
from agentx.utils.helper import iter_to_aiter


class BedrockClient(Client):

    def __init__(self, client: boto3.client):
        self.client = client
        super().__init__()

    def chat_completion(self,
                        *,
                        chat_completion_params: ChatCompletionParams):
        pass

    async def achat_completion(self,
                               *,
                               chat_completion_params: ChatCompletionParams) -> ChatCompletion:
        if chat_completion_params:
            tools = chat_completion_params.tools

            if tools:
                messages = chat_completion_params.messages
                messages = [
                    {
                        "role": "user",
                        "content": [{"text": message["content"]} for message in messages],
                    }
                ]

                inference_config = {
                    "temperature": chat_completion_params.temperature,
                    "maxTokens": chat_completion_params.max_tokens,
                    "topP": chat_completion_params.top_p
                }
                tools_config = {
                    {"tools": chat_completion_params.tools},
                }

                response = self.client.converse(
                    modelId=chat_completion_params.model,
                    messages=messages,
                    inferenceConfig=inference_config,
                    toolConfig=tools_config,
                )

                print(response)

    async def get_tool_json(self, func: typing.Callable) -> dict:
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
            'type': 'function',
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
    def _format_messages(messages: List[Dict[str, str]]) -> str:
        """
        "Converts a list of messages into the necessary prompt format for the model."

        Args:
            messages (List[Dict[str, str]]): A list of dictionaries where each dictionary represents a message.
                                            Each dictionary contains 'role' and 'content' keys.

        Returns:
            str: A formatted string combining all messages, structured with roles capitalized and separated by newlines.
        """
        formatted_messages = []
        for message in messages:
            role = message["role"].capitalize()
            content = message["content"]
            formatted_messages.append(f"\n\n{role}: {content}")

        return "".join(formatted_messages) + "\n\nAssistant:"


