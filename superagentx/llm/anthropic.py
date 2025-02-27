import inspect
import logging

from anthropic import Anthropic, AsyncAnthropic
from fastembed import TextEmbedding
from openai.types.chat import ChatCompletion
from pydantic import typing

from superagentx.llm.models import ChatCompletionParams
from superagentx.llm.client import Client
from superagentx.utils.helper import iter_to_aiter, ptype_to_json_scheme, sync_to_async

logger = logging.getLogger(__name__)


class AnthropicClient(Client):

    def __init__(
            self,
            *,
            client: Anthropic | AsyncAnthropic,
            **kwargs
    ):
        super().__init__(**kwargs)
        self.client = client
        self._embed_model_cli = TextEmbedding(model_name=self._embed_model)

    def chat_completion(
            self,
            *,
            chat_completion_params: ChatCompletionParams
    ) -> ChatCompletion | None:
        params = chat_completion_params.model_dump(exclude_none=True)
        params['model'] = self._model
        return self.client.completions.create(**params)

    async def achat_completion(
            self,
            *,
            chat_completion_params: ChatCompletionParams
    ) -> ChatCompletion | None:
        params = chat_completion_params.model_dump(exclude_none=True)
        params['model'] = self._model
        return await self.client.completions.create(**params)

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
        text = text.replace('\n', ' ')
        return self._embed_model_cli.embed(
            sentences=text,
            **kwargs
        )

    async def aembed(
            self,
            text: str,
            **kwargs
    ):
        return await sync_to_async(
            self.embed,
            text=text,
            **kwargs
        )
