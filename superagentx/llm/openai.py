import asyncio
import inspect
import json
from datetime import datetime
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

_CUSTOM_GENERATE_PATH = "/api/generate"

_CUSTOM_LLM_BASE_URL_ENV = "CUSTOM_LLM_BASE_URL"
_CUSTOM_LLM_API_KEY_ENV = "CUSTOM_LLM_API_KEY"
_CUSTOM_LLM_CLIENT_SECRET_ENV = "CUSTOM_LLM_CLIENT_SECRET"

_CUSTOM_TIMEOUT_SECONDS = 300


class OpenAIClient(Client):

    def __init__(
        self,
        *,
        client,
        **kwargs
    ):
        super().__init__(**kwargs)

        self.client = client

        self.llm_params: dict = kwargs

        # ---------------------------------------------------------
        # Normalize LLM type
        # ---------------------------------------------------------

        raw_llm_type = kwargs.get(
            "llm_type"
        )

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
        # Explicit parameters take precedence over ENV.
        # ---------------------------------------------------------

        self.base_url = (
            kwargs.get("base_url")
            or os.getenv(
                _CUSTOM_LLM_BASE_URL_ENV
            )
        )

        self.api_key = (
            kwargs.get("api_key")
            or os.getenv(
                _CUSTOM_LLM_API_KEY_ENV
            )
        )

        self.client_secret = (
            kwargs.get("client_secret")
            or os.getenv(
                _CUSTOM_LLM_CLIENT_SECRET_ENV
            )
        )

        self.is_custom_client = (
            self.llm_type == LLMType.CUSTOM
        )

        if self.is_custom_client:

            self._validate_custom_config()

        # ---------------------------------------------------------
        # Local embedding model
        # ---------------------------------------------------------

        if (
            self.llm_type == LLMType.DEEPSEEK
            or self.llm_type == LLMType.ANTHROPIC_CLIENT
        ):

            from fastembed import TextEmbedding

            self._embed_model_cli = TextEmbedding()

        # ---------------------------------------------------------
        # Existing OpenAI validation
        # ---------------------------------------------------------

        if (
            not self.is_custom_client
            and self.client is not None
        ):

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
                and not str(
                    self.client.base_url
                ).startswith(
                    _OPEN_API_BASE_URL_PREFIX
                )
                and not OpenAIClient.is_valid_api_key(
                    self.client.api_key
                )
            ):

                logger.info(
                    "OpenAI or Azure hosted Open AI "
                    "client is not valid!"
                )

    # ============================================================
    # CUSTOM CONFIG VALIDATION
    # ============================================================

    def _validate_custom_config(self):

        if not self.base_url:

            raise ValueError(
                "Custom LLM base_url is required. "
                "Provide 'base_url' or set "
                "CUSTOM_LLM_BASE_URL."
            )

        if not self.api_key:

            raise ValueError(
                "Custom LLM api_key is required. "
                "Provide 'api_key' or set "
                "CUSTOM_LLM_API_KEY."
            )

        if not self.client_secret:

            raise ValueError(
                "Custom LLM client_secret is required. "
                "Provide 'client_secret' or set "
                "CUSTOM_LLM_CLIENT_SECRET."
            )

    # ============================================================
    # CUSTOM ENDPOINT
    # ============================================================

    def _get_custom_generate_endpoint(self) -> str:

        base_url = str(
            self.base_url
        ).rstrip("/")

        if base_url.endswith(
            _CUSTOM_GENERATE_PATH
        ):

            return base_url

        return (
            f"{base_url}"
            f"{_CUSTOM_GENERATE_PATH}"
        )

    # ============================================================
    # MESSAGE VALUE
    # ============================================================

    @staticmethod
    def _get_message_value(
        message,
        key: str,
        default=None
    ):

        if isinstance(
            message,
            dict
        ):

            return message.get(
                key,
                default
            )

        return getattr(
            message,
            key,
            default
        )

    # ============================================================
    # MESSAGES → PROMPT
    # ============================================================

    @classmethod
    def _messages_to_prompt(
        cls,
        messages
    ) -> str:

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
            # Handle multimodal/list content
            # -----------------------------------------------------

            if isinstance(
                content,
                list
            ):

                content_parts = []

                for item in content:

                    if isinstance(
                        item,
                        dict
                    ):

                        if item.get(
                            "type"
                        ) == "text":

                            content_parts.append(
                                str(
                                    item.get(
                                        "text",
                                        ""
                                    )
                                )
                            )

                    else:

                        content_parts.append(
                            str(item)
                        )

                content = "\n".join(
                    part
                    for part in content_parts
                    if part
                )

            if content is None:
                content = ""

            content = str(content)

            # -----------------------------------------------------
            # Role mapping
            # -----------------------------------------------------

            if role == "system":

                prompt_parts.append(
                    content
                )

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
                    f"{str(role).capitalize()}: "
                    f"{content}"
                )

        # ---------------------------------------------------------
        # Tell the model to generate assistant response
        # ---------------------------------------------------------

        prompt_parts.append(
            "Assistant:"
        )

        return "\n\n".join(
            prompt_parts
        )

    # ============================================================
    # TOOL DEFINITIONS
    # ============================================================

    async def _get_custom_tool_definitions(
        self,
        params: dict,
    ) -> list[dict]:
        """
        Resolve SuperAgentX tool metadata into OpenAI-style function
        definitions. The DCD gateway does not receive a native `tools`
        request field, so these definitions are injected into the prompt.

        Supported inputs:
        - Already-built OpenAI-style tool dictionaries
        - Callable functions/methods decorated with @tool
        - Objects exposing a callable `func` attribute
        """

        raw_tools = params.get(_TOOLS_KEY_NAME) or []

        if not isinstance(raw_tools, (list, tuple, set)):
            raw_tools = [raw_tools]

        tool_definitions = []

        for tool in raw_tools:

            if isinstance(tool, dict):
                if tool.get("type") == "function":
                    tool_definitions.append(tool)
                elif tool.get("function"):
                    tool_definitions.append({
                        "type": "function",
                        "function": tool["function"],
                    })
                continue

            func = None

            if callable(tool):
                func = tool
            else:
                candidate = getattr(tool, "func", None)
                if callable(candidate):
                    func = candidate

            if func is not None:
                tool_definitions.append(
                    await self.get_tool_json(func=func)
                )

        return tool_definitions

    # ============================================================
    # TOOLS → PROMPT
    # ============================================================

    @staticmethod
    def _tools_to_prompt(
        tool_definitions: list[dict],
    ) -> str:
        """Build deterministic tool instructions for /api/generate."""

        if not tool_definitions:
            return ""

        return (
            "You have access to the following tools.\n\n"
            "TOOL DEFINITIONS:\n"
            f"{json.dumps(tool_definitions, indent=2, ensure_ascii=False)}\n\n"
            "TOOL CALLING RULES:\n"
            "- If a tool is required to answer the user, call the appropriate tool.\n"
            "- Return ONLY one valid JSON object for a tool call.\n"
            "- The JSON object must have exactly these fields: name and arguments.\n"
            "- `name` must exactly match a tool name from TOOL DEFINITIONS.\n"
            "- `arguments` must be a JSON object matching the tool parameters.\n"
            "- Do not add Markdown fences.\n"
            "- Do not return explanatory text when making a tool call.\n"
            "- If no tool is required, answer normally.\n"
        )

    # ============================================================
    # BUILD CUSTOM REQUEST
    # ============================================================

    async def _build_custom_request(
        self,
        chat_completion_params: ChatCompletionParams,
    ):

        params = (
            chat_completion_params.model_dump(
                exclude_none=True
            )
        )

        messages = params.get(
            "messages",
            []
        )

        tool_definitions = await self._get_custom_tool_definitions(
            params
        )

        tool_prompt = self._tools_to_prompt(
            tool_definitions
        )

        prompt = self._messages_to_prompt(
            messages
        )

        if tool_prompt:
            prompt = (
                f"{tool_prompt}\n"
                f"{prompt}"
            )

        # ---------------------------------------------------------
        # Required DCD gateway payload
        # ---------------------------------------------------------

        payload = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
        }

        # ---------------------------------------------------------
        # Forward supported generation parameters
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
        # Required customer gateway headers
        # ---------------------------------------------------------

        headers = {
            "X-Client-Key": self.api_key,
            "X-Client-Secret": self.client_secret,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        return payload, headers

    # ============================================================
    # EXTRACT CUSTOM RESPONSE
    # ============================================================

    @staticmethod
    def _extract_custom_response_content(
        response_data
    ) -> str:

        if response_data is None:

            return ""

        # ---------------------------------------------------------
        # Direct string
        # ---------------------------------------------------------

        if isinstance(
            response_data,
            str
        ):

            return response_data

        if not isinstance(
            response_data,
            dict
        ):

            return str(
                response_data
            )

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

            value = response_data.get(
                field
            )

            if value is not None:

                if isinstance(
                    value,
                    str
                ):

                    return value

                if isinstance(
                    value,
                    dict
                ):

                    nested_content = (
                        value.get("content")
                        or value.get("text")
                        or value.get("response")
                    )

                    if nested_content is not None:

                        return str(
                            nested_content
                        )

                return str(
                    value
                )

        # ---------------------------------------------------------
        # OpenAI-compatible response
        # ---------------------------------------------------------

        choices = response_data.get(
            "choices"
        )

        if (
            choices
            and isinstance(
                choices,
                list
            )
        ):

            first_choice = choices[0]

            if isinstance(
                first_choice,
                dict
            ):

                message = first_choice.get(
                    "message"
                )

                if isinstance(
                    message,
                    dict
                ):

                    content = message.get(
                        "content"
                    )

                    if content is not None:

                        return str(
                            content
                        )

                text = first_choice.get(
                    "text"
                )

                if text is not None:

                    return str(
                        text
                    )

        # ---------------------------------------------------------
        # Nested data
        # ---------------------------------------------------------

        data = response_data.get(
            "data"
        )

        if isinstance(
            data,
            dict
        ):

            nested_content = (
                data.get("response")
                or data.get("content")
                or data.get("text")
                or data.get("answer")
                or data.get("output")
            )

            if nested_content is not None:

                return str(
                    nested_content
                )

        raise ValueError(
            "Unable to extract LLM response "
            "from custom gateway. "
            f"Response: {response_data}"
        )

    # ============================================================
    # CUSTOM TOOL CALL PARSING
    # ============================================================

    @staticmethod
    def _parse_tool_call_content(
        content: str,
    ) -> dict | None:
        """Parse the DCD response string when it represents a tool call."""

        if not isinstance(content, str):
            return None

        candidate = content.strip()

        # Be tolerant of accidental Markdown fences.
        if candidate.startswith("```") and candidate.endswith("```"):
            lines = candidate.splitlines()
            if len(lines) >= 3:
                candidate = "\n".join(lines[1:-1]).strip()

        try:
            parsed = json.loads(candidate)
        except (TypeError, ValueError):
            return None

        if not isinstance(parsed, dict):
            return None

        name = parsed.get("name")
        arguments = parsed.get("arguments")

        if not isinstance(name, str) or not name.strip():
            return None

        if arguments is None:
            arguments = {}

        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except (TypeError, ValueError):
                return None

        if not isinstance(arguments, dict):
            return None

        return {
            "name": name,
            "arguments": arguments,
        }

    # ============================================================
    # CUSTOM RESPONSE → ChatCompletion
    # ============================================================

    @classmethod
    def _convert_custom_response(
        cls,
        response_data,
        model: str
    ) -> ChatCompletion:

        content = (
            cls._extract_custom_response_content(
                response_data
            )
        )

        # ---------------------------------------------------------
        # Metadata
        # ---------------------------------------------------------

        if isinstance(
            response_data,
            dict
        ):

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
            response_id = (
                f"custom-"
                f"{uuid.uuid4().hex}"
            )

        # DCD returns ISO-8601 `created_at` rather than OpenAI's epoch
        # timestamp. Convert it when possible.
        if not created and isinstance(response_data, dict):
            created_at = response_data.get("created_at")

            if created_at:
                try:
                    normalized = str(created_at).replace(
                        "Z",
                        "+00:00"
                    )
                    created = int(
                        datetime.fromisoformat(
                            normalized
                        ).timestamp()
                    )
                except (TypeError, ValueError, OverflowError):
                    created = None

        if not created:
            created = int(time.time())

        # ---------------------------------------------------------
        # DCD usage
        # ---------------------------------------------------------

        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0

        if isinstance(
            response_data,
            dict
        ):
            prompt_tokens = response_data.get(
                "prompt_eval_count",
                0
            ) or 0

            completion_tokens = response_data.get(
                "eval_count",
                0
            ) or 0

        if isinstance(
            usage_data,
            dict
        ):
            prompt_tokens = (
                usage_data.get("prompt_tokens")
                or usage_data.get("input_tokens")
                or prompt_tokens
                or 0
            )

            completion_tokens = (
                usage_data.get("completion_tokens")
                or usage_data.get("output_tokens")
                or completion_tokens
                or 0
            )

            total_tokens = (
                usage_data.get("total_tokens")
                or 0
            )

        if not total_tokens:
            total_tokens = (
                prompt_tokens
                + completion_tokens
            )

        # ---------------------------------------------------------
        # Detect DCD tool-call JSON
        # ---------------------------------------------------------

        tool_call = cls._parse_tool_call_content(
            content
        )

        if tool_call:
            tool_call_id = (
                f"call_"
                f"{uuid.uuid4().hex[:24]}"
            )

            message = {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": tool_call_id,
                        "type": "function",
                        "function": {
                            "name": tool_call["name"],
                            "arguments": json.dumps(
                                tool_call["arguments"],
                                ensure_ascii=False,
                            ),
                        },
                    }
                ],
            }

            finish_reason = "tool_calls"

        else:
            message = {
                "role": "assistant",
                "content": content,
            }

            finish_reason = "stop"

        # ---------------------------------------------------------
        # Create OpenAI-compatible response
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
                        "message": message,
                        "finish_reason": finish_reason,
                    }
                ],
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                },
            }
        )

    # ============================================================
    # ASYNC CUSTOM CHAT
    # ============================================================

    async def _acustom_chat_completion(
        self,
        *,
        chat_completion_params: ChatCompletionParams,
    ) -> ChatCompletion:

        endpoint = (
            self._get_custom_generate_endpoint()
        )

        payload, headers = await self._build_custom_request(
            chat_completion_params
        )

        logger.debug(
            "Calling custom LLM endpoint: %s",
            endpoint
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

                    response_text = (
                        await response.text()
                    )

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

                        response_data = (
                            await response.json()
                        )

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
                "Custom LLM request timed out after "
                f"{_CUSTOM_TIMEOUT_SECONDS} seconds."
            ) from exc

        except aiohttp.ClientError as exc:

            raise RuntimeError(
                f"Custom LLM connection failed: {exc}"
            ) from exc

        return self._convert_custom_response(
            response_data=response_data,
            model=self._model,
        )

    # ============================================================
    # SYNC CUSTOM CHAT
    # ============================================================

    def _custom_chat_completion(
        self,
        *,
        chat_completion_params: ChatCompletionParams,
    ) -> ChatCompletion:

        try:

            asyncio.get_running_loop()

            raise RuntimeError(
                "chat_completion() cannot be called "
                "from an active event loop when using "
                "LLMType.CUSTOM. "
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

        # ---------------------------------------------------------
        # CUSTOM
        # ---------------------------------------------------------

        if self.is_custom_client:

            return self._custom_chat_completion(
                chat_completion_params=chat_completion_params
            )

        # ---------------------------------------------------------
        # Existing OpenAI behavior
        # ---------------------------------------------------------

        params = (
            chat_completion_params.model_dump(
                exclude_none=True
            )
        )

        params["model"] = self._model

        return self.client.chat.completions.create(
            **params
        )

    # ============================================================
    # ASYNC CHAT COMPLETION
    # ============================================================

    async def achat_completion(
        self,
        *,
        chat_completion_params: ChatCompletionParams
    ) -> ChatCompletion:

        # ---------------------------------------------------------
        # CUSTOM
        # ---------------------------------------------------------

        if self.is_custom_client:

            return await self._acustom_chat_completion(
                chat_completion_params=chat_completion_params
            )

        # ---------------------------------------------------------
        # Existing OpenAI behavior
        # ---------------------------------------------------------

        params = (
            chat_completion_params.model_dump(
                exclude_none=True
            )
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

        if self.is_custom_client:

            raise NotImplementedError(
                "Embeddings are not supported by the "
                "custom LLM gateway. "
                "Configure an embedding provider separately."
            )

        text = text.replace(
            "\n",
            " "
        )

        response = (
            self.client.embeddings.create(
                input=[text],
                model=self._embed_model,
                **kwargs
            )
        )

        if (
            self.llm_type == LLMType.DEEPSEEK
            or self.llm_type == LLMType.ANTHROPIC_CLIENT
        ):

            response = (
                self._embed_model_cli.embed(
                    documents=[text],
                    **kwargs
                )
            )

            response = [
                res
                for res in response
            ]

            if response:

                return response[0]

        return self._get_embeddings(
            response
        )

    async def aembed(
        self,
        text: str,
        **kwargs
    ) -> list[float]:

        if self.is_custom_client:

            raise NotImplementedError(
                "Embeddings are not supported by the "
                "custom LLM gateway. "
                "Configure an embedding provider separately."
            )

        text = text.replace(
            "\n",
            " "
        )

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
                res
                async for res
                in iter_to_aiter(response)
            ]

            if response:

                return response[0]

        response = (
            await self.client.embeddings.create(
                input=[text],
                model=self._embed_model,
            )
        )

        return await sync_to_async(
            self._get_embeddings,
            response=response
        )

    # ============================================================
    # API KEY VALIDATION
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

        _doc_str = inspect.getdoc(
            func
        )

        _properties = {}

        _type_hints = typing.get_type_hints(
            func
        )

        _signature = inspect.signature(func)

        _required = []

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
                                f"The "
                                f"{param.replace('_', ' ')}."
                            ),
                            "items": {
                                "type": (
                                    await ptype_to_json_scheme(
                                        param_type.__args__[0].__name__
                                    )
                                )
                            }
                        }

                    else:

                        _properties[param] = {
                            "type": _type,
                            "description": (
                                f"The "
                                f"{param.replace('_', ' ')}."
                            ),
                            "items": {
                                "type": "object"
                            }
                        }

                else:

                    _properties[param] = {
                        "type": _type,
                        "description": (
                            f"The "
                            f"{param.replace('_', ' ')}."
                        )
                    }

        for param_name, parameter in _signature.parameters.items():
            if (
                param_name in _properties
                and parameter.default is inspect.Parameter.empty
            ):
                _required.append(param_name)

        return {
            "type": "function",
            "function": {
                "name": _func_name,
                "description": _doc_str,
                "parameters": {
                    "type": "object",
                    "properties": _properties,
                    "required": _required,
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
                "The cost will be 0. In your config_list, "
                "add field "
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

        tmp_price_1k = OPENAI_PRICE1K[
            model
        ]

        if isinstance(
            tmp_price_1k,
            tuple
        ):

            return (
                tmp_price_1k[0]
                * n_input_tokens
                + tmp_price_1k[1]
                * n_output_tokens
            ) / 1000

        return (
            tmp_price_1k
            * (
                n_input_tokens
                + n_output_tokens
            )
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

            encoding = (
                tiktoken.encoding_for_model(
                    self._model
                )
            )

        except KeyError:

            encoding = (
                tiktoken.get_encoding(
                    "cl100k_base"
                )
            )

        tokens_per_message = 3
        tokens_per_name = 1

        num_tokens = 0

        for message in (
            chat_completion_params.messages
        ):

            num_tokens += (
                tokens_per_message
            )

            content = getattr(
                message,
                "content",
                ""
            )

            if content:

                num_tokens += len(
                    encoding.encode(
                        content
                    )
                )

        num_tokens += 3

        return num_tokens

    # ============================================================
    # ACCOUNT TOKENS
    # ============================================================

    async def account_tokens(
        self,
        chat_completion_params: ChatCompletionParams
    ):

        return await sync_to_async(
            self.count_tokens,
            chat_completion_params
        )