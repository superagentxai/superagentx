import inspect
import logging
import re

from openai import OpenAI, AzureOpenAI, AsyncOpenAI, AsyncAzureOpenAI
from openai.types import CreateEmbeddingResponse
from openai.types.chat.chat_completion import ChatCompletion
from openai.types.completion import Completion
from pydantic import typing

from superagentx.llm import ChatCompletionParams
from superagentx.llm.client import Client
from superagentx.llm.constants import OPENAI_PRICE1K
from superagentx.utils.llm_config import LLMType
from superagentx.utils.helper import sync_to_async, iter_to_aiter, ptype_to_json_scheme

logger = logging.getLogger(__name__)
_OPEN_API_BASE_URL_PREFIX = "https://api.openai.com"
_MODEL_KEY_NAME = 'model'
_SEED_KEY_NAME = 'seed'
_CACHE_SEED = 42
_ASSISTANTS_NAME = 'assistants'
_ASSISTANTS_KEY_NAME = 'name'
_ASSISTANTS_KEY_INSTRUCTIONS = 'instructions'
_TOOLS_KEY_NAME = 'tools'


class OpenAIClient(Client):

    # To set the LLM model

    def __init__(
            self,
            *,
            client: OpenAI | AsyncOpenAI | AzureOpenAI | AsyncAzureOpenAI,
            **kwargs
    ):
        super().__init__(**kwargs)
        self.client = client
        self.llm_params: dict = kwargs
        self.llm_type = kwargs.get("llm_type")
        if self.llm_type == LLMType.DEEPSEEK or self.llm_type == LLMType.ANTHROPIC_CLIENT:
            from fastembed import TextEmbedding
            self._embed_model_cli = TextEmbedding()
        if (
                not isinstance(self.client, OpenAI | AsyncOpenAI | AzureOpenAI | AsyncAzureOpenAI)
                and not str(client.base_url).startswith(_OPEN_API_BASE_URL_PREFIX)
                and not OpenAIClient.is_valid_api_key(self.client.api_key)
        ):
            logger.info(
                "OpenAI or Azure hosted Open AI client, is not valid!"
            )

    def chat_completion(
            self,
            *,
            chat_completion_params: ChatCompletionParams
    ) -> ChatCompletion:
        params = chat_completion_params.model_dump(exclude_none=True)
        params['model'] = self._model  # Get model name from client object attribute and set
        return self.client.chat.completions.create(**params)

    async def achat_completion(
            self,
            *,
            chat_completion_params: ChatCompletionParams
    ) -> ChatCompletion:
        params = chat_completion_params.model_dump(exclude_none=True)
        params['model'] = self._model  # Get model name from client object attribute and set
        chat_completion_response = await self.client.chat.completions.create(**params)
        return chat_completion_response

    @staticmethod
    def _get_embeddings(response: CreateEmbeddingResponse):
        if response and response.data:
            return response.data[0].embedding
        return None

    def embed(
            self,
            text: str,
            **kwargs
    ) -> list[float]:
        """
        Get the embedding for the given text using OpenAI | AzureOpenAI.

        Args:
            text (str): The text to embed.

        Returns:
            list: The embedding vector.
        """
        text = text.replace("\n", " ")
        response = self.client.embeddings.create(
            input=[text],
            model=self._embed_model,
            **kwargs
        )
        if self.llm_type == LLMType.DEEPSEEK or self.llm_type == LLMType.ANTHROPIC_CLIENT:
            response = self._embed_model_cli.embed(
                documents=[text],
                **kwargs
            )
            response = [res for res in response]
            if response:
                return response[0]
        return self._get_embeddings(response)

    async def aembed(
            self,
            text: str,
            **kwargs
    ) -> list[float]:
        """
        Get the embedding for the given text using AsyncOpenAI | AsyncAzureOpenAI.

        Args:
            text (str): The text to embed.

        Returns:
            list: The embedding vector.
        """
        text = text.replace("\n", " ")
        if self.llm_type == LLMType.DEEPSEEK or self.llm_type == LLMType.ANTHROPIC_CLIENT:
            response = await sync_to_async(
                self._embed_model_cli.embed,
                documents=[text],
                **kwargs
            )
            response = [res async for res in iter_to_aiter(response)]
            if response:
                return response[0]
        response = await self.client.embeddings.create(
            input=[text],
            model=self._embed_model,
        )
        return await sync_to_async(
            self._get_embeddings,
            response=response
        )

    @staticmethod
    def is_valid_api_key(api_key: str) -> bool:
        """Determine if input is valid OpenAI API key.

        Args:
            api_key (str): An input string to be validated.

        Returns:
            bool: A boolean that indicates if input is valid OpenAI API key.
        """
        api_key_re = re.compile(r"^sk-([A-Za-z0-9]+(-+[A-Za-z0-9]+)*-)?[A-Za-z0-9]{32,}$")
        return bool(re.fullmatch(api_key_re, api_key))

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

    @staticmethod
    def cost(response: ChatCompletion | Completion) -> float:
        """Calculate the cost of the response."""
        model = response.model
        if model not in OPENAI_PRICE1K:
            # log warning that the model is not found
            logger.warning(
                f'Model {model} is not found. The cost will be 0. In your config_list, add field {{"price" : ['
                f'prompt_price_per_1k, completion_token_price_per_1k]}} for customized pricing.'
            )
            return 0.0

        n_input_tokens = response.usage.prompt_tokens if response.usage is not None else 0.0
        n_output_tokens = response.usage.completion_tokens if response.usage is not None else 0.0
        if n_output_tokens is None:
            n_output_tokens = 0.0
        tmp_price_1k = OPENAI_PRICE1K[model]
        # First value is input token rate, second value is output token rate
        if isinstance(tmp_price_1k, tuple):
            return (tmp_price_1k[0] * n_input_tokens + tmp_price_1k[1] * n_output_tokens) / 1000
        return tmp_price_1k * (n_input_tokens + n_output_tokens) / 1000

    def __replace_instance_values(self, source_instance: ChatCompletionParams):
        params = self.llm_params.keys()
        for _key in params:
            if _key in source_instance.__fields__:
                setattr(source_instance, _key, self.llm_params[_key])
        return source_instance
