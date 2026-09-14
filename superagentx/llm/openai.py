import asyncio
import inspect
import logging
import os
import re
import time
import typing
import uuid

import aiohttp

from openai import (
    OpenAI,
    AzureOpenAI,
    AsyncOpenAI,
    AsyncAzureOpenAI,
)
from openai.types import CreateEmbeddingResponse
from openai.types.chat.chat_completion import ChatCompletion
from openai.types.completion import Completion
from typing import Callable

from superagentx.llm import ChatCompletionParams
from superagentx.llm.client import Client
from superagentx.llm.constants import OPENAI_PRICE1K
from superagentx.utils.llm_config import LLMType
from superagentx.utils.helper import (
    sync_to_async,
    iter_to_aiter,
    ptype_to_json_scheme,
)


logger = logging.getLogger(__name__)


_OPEN_API_BASE_URL_PREFIX = "https://api.openai.com"

_MODEL_KEY_NAME = "model"
_SEED_KEY_NAME = "seed"
_CACHE_SEED = 42

_ASSISTANTS_NAME = "assistants"
_ASSISTANTS_KEY_NAME = "name"
_ASSISTANTS_KEY_INSTRUCTIONS = "instructions"
_TOOLS_KEY_NAME = "tools"

_CUSTOM_CHAT_PATH = "/api/chat"

_CUSTOM_LLM_BASE_URL_ENV = "CUSTOM_LLM_BASE_URL"
_CUSTOM_LLM_API_KEY_ENV = "CUSTOM_LLM_API_KEY"
_CUSTOM_LLM_CLIENT_SECRET_ENV = "CUSTOM_LLM_CLIENT_SECRET"

_CUSTOM_TIMEOUT_SECONDS = 300


class OpenAIClient(Client):

    def __init__(
        self,
        *,
        client: OpenAI | AsyncOpenAI | AzureOpenAI | AsyncAzureOpenAI,
        **kwargs
    ):
        super().__init__(**kwargs)

        self.client = client
        self.llm_params: dict = kwargs

        # Normalize llm_type
        raw_llm_type = kwargs.get("llm_type")

        try:
            self.llm_type = (
                LLMType(raw_llm_type)
                if raw_llm_type is not None
                else None
            )
        except ValueError:
            self.llm_type = raw_llm_type

        # ---------------------------------------------------------
        # Custom LLM configuration
        #
        # Parameter has priority over ENV
        # ---------------------------------------------------------

        self.base_url = kwargs.get(
            "base_url",
            os.getenv(_CUSTOM_LLM_BASE_URL_ENV)
        )

        self.api_key = kwargs.get(
            "api_key",
            os.getenv(_CUSTOM_LLM_API_KEY_ENV)
        )

        self.client_secret = kwargs.get(
            "client_secret",
            os.getenv(_CUSTOM_LLM_CLIENT_SECRET_ENV)
        )

        self.is_custom_client = (
            self.llm_type == LLMType.CUSTOM
        )

        if self.is_custom_client:
            self._validate_custom_config()

        # ---------------------------------------------------------
        # Local embedding model for providers that don't expose
        # OpenAI-compatible embeddings
        # ---------------------------------------------------------

        if (
            self.llm_type == LLMType.DEEPSEEK
            or self.llm_type == LLMType.ANTHROPIC_CLIENT
        ):
            from fastembed import TextEmbedding

            self._embed_model_cli = TextEmbedding()

        # ---------------------------------------------------------
        # Existing OpenAI client validation
        # ---------------------------------------------------------

        if not self.is_custom_client:

            if (
                not isinstance(
                    self.client,
                    (
                        OpenAI,
                        AsyncOpenAI,
                        AzureOpenAI,
                        AsyncAzureOpenAI,
                    ),
                )
                and not str(client.base_url).startswith(
                    _OPEN_API_BASE_URL_PREFIX
                )
                and not OpenAIClient.is_valid_api_key(
                    self.client.api_key
                )
            ):
                logger.info(
                    "OpenAI or Azure hosted Open AI client, "
                    "is not valid!"
                )

    # ============================================================
    # CUSTOM LLM
    # ============================================================

    def _validate_custom_config(self):
        """
        Validate custom LLM configuration.

        Configuration can come from either:
            1. llm_config parameters
            2. Environment variables

        Explicit parameters have priority over ENV.
        """

        if not self.base_url:
            raise ValueError(
                "Custom LLM base_url is required. "
                "Provide 'base_url' in llm_config or set "
                f"{_CUSTOM_LLM_BASE_URL_ENV}."
            )

        if not self.api_key:
            raise ValueError(
                "Custom LLM api_key is required. "
                "Provide 'api_key' in llm_config or set "
                f"{_CUSTOM_LLM_API_KEY_ENV}."
            )

        if not self.client_secret:
            raise ValueError(
                "Custom LLM client_secret is required. "
                "Provide 'client_secret' in llm_config or set "
                f"{_CUSTOM_LLM_CLIENT_SECRET_ENV}."
            )

    def _get_custom_chat_endpoint(self) -> str:
        """
        Build the custom chat endpoint.

        Example:

            base_url:
                https://gateway.example.com

            endpoint:
                https://gateway.example.com/api/chat
        """

        base_url = str(self.base_url).rstrip("/")

        if base_url.endswith(_CUSTOM_CHAT_PATH):
            return base_url

        return f"{base_url}{_CUSTOM_CHAT_PATH}"

    @staticmethod
    def _get_message_value(message, key: str, default=None):
        """
        Read a message property from either:
            - dict
            - Pydantic/OpenAI message object
        """

        if isinstance(message, dict):
            return message.get(key, default)

        return getattr(message, key, default)

    @classmethod
    def _messages_to_prompt(cls, messages) -> str:
        """
        Convert OpenAI/SuperAgentX messages into the custom
        gateway prompt format.

        Example:

        System:
            You are a helpful assistant.

        User:
            What is microservices architecture?

        Result:

        You are a helpful assistant.

        User: What is microservices architecture?
        Assistant:
        """

        prompt_parts = []

        for message in messages:

            role = cls._get_message_value(
                message,
                "role",
                "user"
            )

            content = cls._get_message_value(
                message,
                "content",
                ""
            )

            # -----------------------------------------------------
            # Handle list content
            # -----------------------------------------------------

            if isinstance(content, list):

                content_parts = []

                for item in content:

                    if isinstance(item, dict):

                        if item.get("type") == "text":
                            content_parts.append(
                                str(item.get("text", ""))
                            )

                    else:
                        content_parts.append(str(item))

                content = "\n".join(
                    part for part in content_parts if part
                )

            if content is None:
                content = ""

            content = str(content)

            # -----------------------------------------------------
            # Map roles to gateway prompt format
            # -----------------------------------------------------

            if role == "system":
                prompt_parts.append(content)

            elif role == "user":
                prompt_parts.append(
                    f"User: {content}"
                )

            elif role == "assistant":
                prompt_parts.append(
                    f"Assistant: {content}"
                )

            elif role == "tool":
                prompt_parts.append(
                    f"Tool: {content}"
                )

            else:
                prompt_parts.append(
                    f"{role.capitalize()}: {content}"
                )

        # The custom gateway expects the model to generate
        # the next Assistant response.
        prompt_parts.append("Assistant:")

        return "\n\n".join(prompt_parts)

    def _build_custom_request(
        self,
        chat_completion_params: ChatCompletionParams,
    ):
        """
        Build request payload and headers for the custom gateway.
        """

        params = chat_completion_params.model_dump(
            exclude_none=True
        )

        messages = params.get("messages", [])

        prompt = self._messages_to_prompt(messages)

        # ---------------------------------------------------------
        # Gateway payload
        # ---------------------------------------------------------

        payload = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
        }

        # ---------------------------------------------------------
        # Forward common generation parameters when supported
        # ---------------------------------------------------------

        supported_params = (
            "temperature",
            "top_p",
            "max_tokens",
            "stop",
            "seed",
        )

        for key in supported_params:

            if key in params:
                payload[key] = params[key]

        # ---------------------------------------------------------
        # Gateway headers
        # ---------------------------------------------------------

        headers = {
            "X-Client-Key": self.api_key,
            "X-Client-Secret": self.client_secret,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        return payload, headers

    @staticmethod
    def _extract_custom_response_content(
        response_data,
    ) -> str:
        """
        Extract generated text from different possible gateway
        response formats.

        Supported examples:

            {"response": "..."}
            {"content": "..."}
            {"text": "..."}
            {"answer": "..."}
            {"output": "..."}
            {"generated_text": "..."}

        Also supports OpenAI-style:

            {
                "choices": [
                    {
                        "message": {
                            "content": "..."
                        }
                    }
                ]
            }
        """

        if response_data is None:
            return ""

        # ---------------------------------------------------------
        # Direct string response
        # ---------------------------------------------------------

        if isinstance(response_data, str):
            return response_data

        if not isinstance(response_data, dict):
            return str(response_data)

        # ---------------------------------------------------------
        # Direct response fields
        # ---------------------------------------------------------

        direct_fields = (
            "response",
            "content",
            "text",
            "answer",
            "output",
            "generated_text",
        )

        for field in direct_fields:

            value = response_data.get(field)

            if value is not None:

                if isinstance(value, str):
                    return value

                if isinstance(value, dict):
                    nested_content = (
                        value.get("content")
                        or value.get("text")
                        or value.get("response")
                    )

                    if nested_content is not None:
                        return str(nested_content)

                return str(value)

        # ---------------------------------------------------------
        # OpenAI-compatible response
        # ---------------------------------------------------------

        choices = response_data.get("choices")

        if choices and isinstance(choices, list):

            first_choice = choices[0]

            if isinstance(first_choice, dict):

                message = first_choice.get("message")

                if isinstance(message, dict):

                    content = message.get("content")

                    if content is not None:
                        return str(content)

                text = first_choice.get("text")

                if text is not None:
                    return str(text)

        # ---------------------------------------------------------
        # Nested data response
        # ---------------------------------------------------------

        data = response_data.get("data")

        if isinstance(data, dict):

            nested_content = (
                data.get("response")
                or data.get("content")
                or data.get("text")
                or data.get("answer")
                or data.get("output")
            )

            if nested_content is not None:
                return str(nested_content)

        raise ValueError(
            "Unable to extract LLM response from custom gateway. "
            f"Response: {response_data}"
        )

    @classmethod
    def _convert_custom_response(
        cls,
        response_data,
        model: str,
    ) -> ChatCompletion:
        """
        Convert the custom gateway response into an OpenAI
        compatible ChatCompletion object.

        This allows the rest of SuperAgentX to remain unchanged.
        """

        content = cls._extract_custom_response_content(
            response_data
        )

        # ---------------------------------------------------------
        # Response metadata
        # ---------------------------------------------------------

        if isinstance(response_data, dict):

            response_id = response_data.get("id")

            created = response_data.get("created")

            response_model = (
                response_data.get("model")
                or model
            )

            usage_data = response_data.get(
                "usage",
                {}
            )

        else:

            response_id = None
            created = None
            response_model = model
            usage_data = {}

        if not response_id:
            response_id = f"custom-{uuid.uuid4().hex}"

        if not created:
            created = int(time.time())

        # ---------------------------------------------------------
        # Usage
        # ---------------------------------------------------------

        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0

        if isinstance(usage_data, dict):

            prompt_tokens = (
                usage_data.get("prompt_tokens")
                or usage_data.get("input_tokens")
                or 0
            )

            completion_tokens = (
                usage_data.get("completion_tokens")
                or usage_data.get("output_tokens")
                or 0
            )

            total_tokens = (
                usage_data.get("total_tokens")
                or (
                    prompt_tokens
                    + completion_tokens
                )
            )

        # ---------------------------------------------------------
        # Build OpenAI-compatible response
        # ---------------------------------------------------------

        return ChatCompletion.model_validate(
            {
                "id": response_id,
                "object": "chat.completion",
                "created": created,
                "model": response_model,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": content,
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                },
            }
        )

    async def _acustom_chat_completion(
        self,
        *,
        chat_completion_params: ChatCompletionParams,
    ) -> ChatCompletion:

        endpoint = self._get_custom_chat_endpoint()

        payload, headers = self._build_custom_request(
            chat_completion_params
        )

        logger.debug(
            "Calling custom LLM endpoint: %s",
            endpoint,
        )

        timeout = aiohttp.ClientTimeout(
            total=_CUSTOM_TIMEOUT_SECONDS
        )

        try:

            async with aiohttp.ClientSession(
                timeout=timeout
            ) as session:

                async with session.post(
                    endpoint,
                    headers=headers,
                    json=payload,
                ) as response:

                    response_text = await response.text()

                    # -------------------------------------------------
                    # HTTP error
                    # -------------------------------------------------

                    if response.status >= 400:

                        logger.error(
                            "Custom LLM request failed. "
                            "Status=%s Response=%s",
                            response.status,
                            response_text,
                        )

                        raise RuntimeError(
                            "Custom LLM request failed: "
                            f"HTTP {response.status}: "
                            f"{response_text}"
                        )

                    # -------------------------------------------------
                    # Parse JSON
                    # -------------------------------------------------

                    try:
                        response_data = await response.json()

                    except Exception as exc:

                        logger.error(
                            "Custom LLM returned invalid JSON: %s",
                            response_text,
                        )

                        raise RuntimeError(
                            "Custom LLM returned invalid JSON: "
                            f"{response_text}"
                        ) from exc

        except asyncio.TimeoutError as exc:

            raise RuntimeError(
                f"Custom LLM request timed out after "
                f"{_CUSTOM_TIMEOUT_SECONDS} seconds."
            ) from exc

        except aiohttp.ClientError as exc:

            raise RuntimeError(
                f"Custom LLM connection failed: {exc}"
            ) from exc

        # ---------------------------------------------------------
        # Convert to OpenAI ChatCompletion
        # ---------------------------------------------------------

        return self._convert_custom_response(
            response_data=response_data,
            model=self._model,
        )

    def _custom_chat_completion(
        self,
        *,
        chat_completion_params: ChatCompletionParams,
    ) -> ChatCompletion:

        try:
            asyncio.get_running_loop()

            # A running event loop already exists.
            raise RuntimeError(
                "chat_completion() cannot be called from an "
                "active event loop when using LLMType.CUSTOM. "
                "Use 'await achat_completion()' instead."
            )

        except RuntimeError as exc:

            if str(exc).startswith(
                "chat_completion() cannot"
            ):
                raise

        return asyncio.run(
            self._acustom_chat_completion(
                chat_completion_params=chat_completion_params
            )
        )

    # ============================================================
    # CHAT COMPLETION
    # ============================================================

    def chat_completion(
        self,
        *,
        chat_completion_params: ChatCompletionParams
    ) -> ChatCompletion:

        if self.is_custom_client:

            return self._custom_chat_completion(
                chat_completion_params=chat_completion_params
            )

        params = chat_completion_params.model_dump(
            exclude_none=True
        )

        params["model"] = self._model

        return self.client.chat.completions.create(
            **params
        )

    async def achat_completion(
        self,
        *,
        chat_completion_params: ChatCompletionParams
    ) -> ChatCompletion:

        if self.is_custom_client:

            return await self._acustom_chat_completion(
                chat_completion_params=chat_completion_params
            )

        params = chat_completion_params.model_dump(
            exclude_none=True
        )

        params["model"] = self._model

        return await self.client.chat.completions.create(
            **params
        )

    # ============================================================
    # EMBEDDINGS
    # ============================================================

    @staticmethod
    def _get_embeddings(
        response: CreateEmbeddingResponse
    ):
        if response and response.data:
            return response.data[0].embedding

        return None

    def embed(
        self,
        text: str,
        **kwargs
    ) -> list[float]:

        # Custom gateway currently exposes only /api/chat.
        if self.is_custom_client:
            raise NotImplementedError(
                "Embeddings are not supported by the custom LLM "
                "gateway. Configure an embedding provider separately."
            )

        text = text.replace("\n", " ")

        response = self.client.embeddings.create(
            input=[text],
            model=self._embed_model,
            **kwargs
        )

        if (
            self.llm_type == LLMType.DEEPSEEK
            or self.llm_type == LLMType.ANTHROPIC_CLIENT
        ):

            response = self._embed_model_cli.embed(
                documents=[text],
                **kwargs
            )

            response = [
                res
                for res in response
            ]

            if response:
                return response[0]

        return self._get_embeddings(response)

    async def aembed(
        self,
        text: str,
        **kwargs
    ) -> list[float]:

        # Custom gateway currently exposes only /api/chat.
        if self.is_custom_client:
            raise NotImplementedError(
                "Embeddings are not supported by the custom LLM "
                "gateway. Configure an embedding provider separately."
            )

        text = text.replace("\n", " ")

        if (
            self.llm_type == LLMType.DEEPSEEK
            or self.llm_type == LLMType.ANTHROPIC_CLIENT
        ):

            response = await sync_to_async(
                self._embed_model_cli.embed,
                documents=[text],
                **kwargs
            )

            response = [
                res async for res in iter_to_aiter(response)
            ]

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

    # ============================================================
    # API KEY
    # ============================================================

    @staticmethod
    def is_valid_api_key(
        api_key: str
    ) -> bool:

        if not api_key:
            return False

        api_key_re = re.compile(
            r"^sk-([A-Za-z0-9]+(-+[A-Za-z0-9]+)*-)?"
            r"[A-Za-z0-9]{32,}$"
        )

        return bool(
            re.fullmatch(
                api_key_re,
                api_key
            )
        )

    # ============================================================
    # TOOL JSON
    # ============================================================

    async def get_tool_json(
        self,
        func: Callable
    ) -> dict:

        _func_name = func.__name__

        _doc_str = inspect.getdoc(func)

        _properties = {}

        _type_hints = typing.get_type_hints(func)

        async for param, param_type in iter_to_aiter(
            _type_hints.items()
        ):

            if param != "return":

                _type = await ptype_to_json_scheme(
                    param_type.__name__
                )

                if _type == "array":

                    if hasattr(
                        param_type,
                        "__args__"
                    ):

                        _properties[param] = {
                            "type": _type,
                            "description": (
                                f"The {param.replace('_', ' ')}."
                            ),
                            "items": {
                                "type": await ptype_to_json_scheme(
                                    param_type.__args__[0].__name__
                                )
                            }
                        }

                    else:

                        _properties[param] = {
                            "type": _type,
                            "description": (
                                f"The {param.replace('_', ' ')}."
                            ),
                            "items": {
                                "type": "object"
                            }
                        }

                else:

                    _properties[param] = {
                        "type": _type,
                        "description": (
                            f"The {param.replace('_', ' ')}."
                        )
                    }

        return {
            "type": "function",
            "function": {
                "name": _func_name,
                "description": _doc_str,
                "parameters": {
                    "type": "object",
                    "properties": _properties,
                    "required": list(
                        _properties.keys()
                    ),
                }
            }
        }

    # ============================================================
    # COST
    # ============================================================

    @staticmethod
    def cost(
        response: ChatCompletion | Completion
    ) -> float:

        model = response.model

        if model not in OPENAI_PRICE1K:

            logger.warning(
                f"Model {model} is not found. "
                "The cost will be 0. "
                "In your config_list, add field "
                '{"price" : [prompt_price_per_1k, '
                'completion_token_price_per_1k]} '
                "for customized pricing."
            )

            return 0.0

        n_input_tokens = (
            response.usage.prompt_tokens
            if response.usage is not None
            else 0.0
        )

        n_output_tokens = (
            response.usage.completion_tokens
            if response.usage is not None
            else 0.0
        )

        if n_output_tokens is None:
            n_output_tokens = 0.0

        tmp_price_1k = OPENAI_PRICE1K[model]

        if isinstance(tmp_price_1k, tuple):

            return (
                tmp_price_1k[0] * n_input_tokens
                + tmp_price_1k[1] * n_output_tokens
            ) / 1000

        return (
            tmp_price_1k
            * (n_input_tokens + n_output_tokens)
        ) / 1000

    # ============================================================
    # REPLACE INSTANCE VALUES
    # ============================================================

    def __replace_instance_values(
        self,
        source_instance: ChatCompletionParams
    ):

        params = self.llm_params.keys()

        for _key in params:

            if _key in source_instance.__fields__:

                setattr(
                    source_instance,
                    _key,
                    self.llm_params[_key]
                )

        return source_instance

    # ============================================================
    # TOKEN COUNT
    # ============================================================

    def count_tokens(
        self,
        chat_completion_params: ChatCompletionParams
    ):

        import tiktoken

        try:

            encoding = tiktoken.encoding_for_model(
                self._model
            )

        except KeyError:

            encoding = tiktoken.get_encoding(
                "cl100k_base"
            )

        tokens_per_message = 3
        tokens_per_name = 1

        num_tokens = 0

        for message in chat_completion_params.messages:

            num_tokens += tokens_per_message

            content = getattr(
                message,
                "content",
                ""
            )

            if content:
                num_tokens += len(
                    encoding.encode(content)
                )

        num_tokens += 3

        return num_tokens

    async def account_tokens(
        self,
        chat_completion_params: ChatCompletionParams
    ):

        return await sync_to_async(
            self.count_tokens,
            chat_completion_params
        )