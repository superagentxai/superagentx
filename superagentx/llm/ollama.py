import inspect
import json
import logging
import os
import re
import time
import uuid
import typing

from typing import Callable

import httpx

from openai.types import CompletionUsage
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionMessage,
    ChatCompletionMessageToolCall,
)
from openai.types.chat.chat_completion import Choice

from superagentx.llm import ChatCompletionParams
from superagentx.llm.client import Client
from superagentx.utils.helper import (
    iter_to_aiter,
    ptype_to_json_scheme,
    sync_to_async,
)


_retries = 5

logger = logging.getLogger(__name__)


class OllamaClient(Client):

    # ============================================================
    # INIT
    # ============================================================

    def __init__(
        self,
        *,
        client=None,
        host: str | None = None,
        api_key: str | None = None,
        client_secret: str | None = None,
        **kwargs
    ):
        super().__init__(**kwargs)

        self.host = (
            host
            or os.getenv("OLLAMA_HOST")
            or ""
        ).rstrip("/")

        self.api_key = (
            api_key
            or os.getenv("OLLAMA_API_KEY")
        )

        self.client_secret = (
            client_secret
            or os.getenv("OLLAMA_CLIENT_SECRET")
        )

        self.kwargs = kwargs

        if not self.host:
            raise ValueError(
                "OLLAMA_HOST is required."
            )

        if not self.api_key:
            raise ValueError(
                "OLLAMA_API_KEY is required."
            )

        if not self.client_secret:
            raise ValueError(
                "OLLAMA_CLIENT_SECRET is required."
            )

        # --------------------------------------------------------
        # DCD Gateway headers
        # --------------------------------------------------------

        self.headers = {
            "Content-Type": "application/json",
            "X-Client-Key": self.api_key,
            "X-Client-Secret": self.client_secret,
        }

        # --------------------------------------------------------
        # HTTP clients
        #
        # Keep both clients so sync and async methods work.
        # --------------------------------------------------------

        self._async_client = httpx.AsyncClient(
            base_url=self.host,
            headers=self.headers,
            timeout=120.0,
        )

        self._sync_client = httpx.Client(
            base_url=self.host,
            headers=self.headers,
            timeout=120.0,
        )

        # --------------------------------------------------------
        # Keep supplied client only for backward compatibility.
        # Do NOT use it for HTTP calls.
        # --------------------------------------------------------

        self.client = client

        logger.debug(
            "Initialized Ollama HTTP client: host=%s",
            self.host,
        )

    # ============================================================
    # CLOSE
    # ============================================================

    async def aclose(self):
        """Close the async HTTP client."""

        if self._async_client:
            await self._async_client.aclose()

    def close(self):
        """Close the sync HTTP client."""

        if self._sync_client:
            self._sync_client.close()

    # ============================================================
    # OPTIONS
    # ============================================================

    @staticmethod
    def _build_ollama_options(
        chat_completion_params: ChatCompletionParams,
    ) -> dict:
        """
        Convert SuperAgentX generation parameters into
        Ollama options.
        """

        options = {}

        # --------------------------------------------------------
        # Temperature
        # --------------------------------------------------------

        temperature = getattr(
            chat_completion_params,
            "temperature",
            None,
        )

        if temperature is not None:
            options["temperature"] = temperature

        # --------------------------------------------------------
        # Top P
        # --------------------------------------------------------

        top_p = getattr(
            chat_completion_params,
            "top_p",
            None,
        )

        if top_p is not None:
            options["top_p"] = top_p

        # --------------------------------------------------------
        # Max tokens
        # --------------------------------------------------------

        max_tokens = getattr(
            chat_completion_params,
            "max_tokens",
            None,
        )

        if max_tokens is not None:
            options["num_predict"] = max_tokens

        # --------------------------------------------------------
        # Seed
        # --------------------------------------------------------

        seed = getattr(
            chat_completion_params,
            "seed",
            None,
        )

        if seed is not None:
            options["seed"] = seed

        # --------------------------------------------------------
        # Stop
        # --------------------------------------------------------

        stop = getattr(
            chat_completion_params,
            "stop",
            None,
        )

        if stop is not None:

            if isinstance(stop, str):

                options["stop"] = [
                    stop
                ]

            elif isinstance(
                stop,
                (list, tuple),
            ):

                options["stop"] = list(
                    stop
                )

        return options

    # ============================================================
    # MESSAGE NORMALIZATION
    # ============================================================

    @staticmethod
    def _normalize_messages(
        messages,
    ) -> list[dict]:
        """
        Convert SuperAgentX/OpenAI message objects into
        plain dictionaries accepted by DCD/Ollama.
        """

        normalized_messages = []

        for message in messages or []:

            # ----------------------------------------------------
            # Dict message
            # ----------------------------------------------------

            if isinstance(
                message,
                dict,
            ):

                message_dict = dict(
                    message
                )

            # ----------------------------------------------------
            # Pydantic / object message
            # ----------------------------------------------------

            else:

                role = getattr(
                    message,
                    "role",
                    "user",
                )

                content = getattr(
                    message,
                    "content",
                    "",
                )

                message_dict = {
                    "role": role,
                    "content": content,
                }

                # ------------------------------------------------
                # Tool calls
                # ------------------------------------------------

                tool_calls = getattr(
                    message,
                    "tool_calls",
                    None,
                )

                if tool_calls is not None:

                    normalized_tool_calls = []

                    for tool_call in tool_calls:

                        if isinstance(
                            tool_call,
                            dict,
                        ):

                            normalized_tool_calls.append(
                                tool_call
                            )

                        elif hasattr(
                            tool_call,
                            "model_dump",
                        ):

                            normalized_tool_calls.append(
                                tool_call.model_dump(
                                    exclude_none=True
                                )
                            )

                        else:

                            normalized_tool_calls.append(
                                tool_call
                            )

                    message_dict[
                        "tool_calls"
                    ] = normalized_tool_calls

                # ------------------------------------------------
                # Tool call ID
                # ------------------------------------------------

                tool_call_id = getattr(
                    message,
                    "tool_call_id",
                    None,
                )

                if tool_call_id is not None:

                    message_dict[
                        "tool_call_id"
                    ] = tool_call_id

                # ------------------------------------------------
                # Name
                # ------------------------------------------------

                name = getattr(
                    message,
                    "name",
                    None,
                )

                if name is not None:

                    message_dict[
                        "name"
                    ] = name

            # ----------------------------------------------------
            # Content normalization
            # ----------------------------------------------------

            content = message_dict.get(
                "content"
            )

            if content is None:

                message_dict[
                    "content"
                ] = ""

            elif isinstance(
                content,
                list,
            ):

                message_dict[
                    "content"
                ] = content

            else:

                message_dict[
                    "content"
                ] = str(
                    content
                )

            normalized_messages.append(
                message_dict
            )

        return normalized_messages

    # ============================================================
    # TOOL NORMALIZATION
    # ============================================================

    @staticmethod
    def _normalize_tools(
        tools,
    ) -> list[dict]:
        """
        Normalize tool definitions before sending to DCD/Ollama.
        """

        if not tools:
            return []

        normalized_tools = []

        for tool in tools:

            # ----------------------------------------------------
            # Already a dict
            # ----------------------------------------------------

            if isinstance(
                tool,
                dict,
            ):

                normalized_tools.append(
                    tool
                )

                continue

            # ----------------------------------------------------
            # Pydantic
            # ----------------------------------------------------

            if hasattr(
                tool,
                "model_dump",
            ):

                normalized_tools.append(
                    tool.model_dump(
                        exclude_none=True
                    )
                )

                continue

            # ----------------------------------------------------
            # Older Pydantic
            # ----------------------------------------------------

            if hasattr(
                tool,
                "dict",
            ):

                normalized_tools.append(
                    tool.dict()
                )

                continue

            logger.warning(
                "Skipping unsupported tool type: %s",
                type(tool),
            )

        return normalized_tools

    # ============================================================
    # TOOL CHOICE
    # ============================================================

    @staticmethod
    def _normalize_tool_choice(
        tool_choice
    ):
        """
        Normalize OpenAI-style tool_choice.
        """

        if tool_choice is None:
            return None

        if isinstance(
            tool_choice,
            str,
        ):

            return tool_choice

        if isinstance(
            tool_choice,
            dict,
        ):

            return tool_choice

        if hasattr(
            tool_choice,
            "model_dump",
        ):

            return tool_choice.model_dump(
                exclude_none=True
            )

        return tool_choice

    # ============================================================
    # BUILD CHAT PAYLOAD
    # ============================================================

    def _build_chat_payload(
        self,
        chat_completion_params: ChatCompletionParams,
    ) -> dict:

        params = (
            chat_completion_params.model_dump(
                exclude_none=True
            )
        )

        messages = self._normalize_messages(
            params.get(
                "messages",
                [],
            )
        )

        tools = self._normalize_tools(
            params.get(
                "tools"
            )
            or []
        )

        options = self._build_ollama_options(
            chat_completion_params
        )

        payload = {
            "model": "gpt-oss:20b",
            "messages": messages,
            "stream": False,
        }

        # --------------------------------------------------------
        # Generation options
        # --------------------------------------------------------

        if options:

            payload[
                "options"
            ] = options

        # --------------------------------------------------------
        # Native tools
        #
        # IMPORTANT:
        # Do NOT send format=json when tools exist.
        # --------------------------------------------------------

        if tools:

            payload[
                "tools"
            ] = tools

            tool_choice = (
                self._normalize_tool_choice(
                    params.get(
                        "tool_choice"
                    )
                )
            )

            if tool_choice is not None:

                payload[
                    "tool_choice"
                ] = tool_choice

        else:

            # ----------------------------------------------------
            # JSON format only when requested
            # ----------------------------------------------------

            response_format = (
                params.get(
                    "response_format"
                )
            )

            if response_format:

                if isinstance(
                    response_format,
                    dict,
                ):

                    response_type = (
                        response_format.get(
                            "type"
                        )
                    )

                    if response_type in (
                        "json",
                        "json_object",
                    ):

                        payload[
                            "format"
                        ] = "json"

                else:

                    payload[
                        "format"
                    ] = response_format

        return payload

    # ============================================================
    # HTTP ERROR
    # ============================================================

    @staticmethod
    def _raise_http_error(
        response: httpx.Response,
    ):
        """
        Convert HTTP errors into a useful exception.
        """

        if response.is_success:
            return

        try:

            error_body = response.json()

        except Exception:

            error_body = response.text

        raise RuntimeError(
            "Ollama gateway request failed: "
            f"HTTP {response.status_code}: "
            f"{error_body}"
        )

    # ============================================================
    # CHAT COMPLETION - SYNC
    # ============================================================

    def chat_completion(
        self,
        *,
        chat_completion_params: ChatCompletionParams
    ) -> ChatCompletion | None:

        if not chat_completion_params:
            return None

        payload = self._build_chat_payload(
            chat_completion_params
        )

        logger.debug(
            "Calling Ollama gateway: "
            "model=%s tools=%s",
            self._model,
            len(
                payload.get(
                    "tools",
                    [],
                )
            ),
        )

        logger.debug(
            "Ollama request payload: %s",
            payload,
        )

        try:

            response = self._sync_client.post(
                "/api/chat",
                json=payload,
            )

            self._raise_http_error(
                response
            )

            response_data = (
                response.json()
            )

        except Exception as e:

            logger.exception(
                "Failed to get response "
                "from Ollama gateway"
            )

            raise RuntimeError(
                "Failed to get response from "
                f"Ollama gateway: {e}"
            ) from e

        logger.debug(
            "Ollama response: %s",
            response_data,
        )

        return (
            self.__prepare_ollama_formatted_output(
                response=response_data,
                model=self._model,
            )
        )

    # ============================================================
    # CHAT COMPLETION - ASYNC
    # ============================================================

    async def achat_completion(
        self,
        *,
        chat_completion_params: ChatCompletionParams
    ) -> ChatCompletion | None:

        if not chat_completion_params:
            return None

        payload = self._build_chat_payload(
            chat_completion_params
        )

        logger.debug(
            "Calling async Ollama gateway: "
            "model=%s tools=%s",
            self._model,
            len(
                payload.get(
                    "tools",
                    [],
                )
            ),
        )

        logger.debug(
            "Ollama request payload: %s",
            payload,
        )

        try:

            response = (
                await self._async_client.post(
                    "/api/chat",
                    json=payload,
                )
            )

            self._raise_http_error(
                response
            )

            response_data = (
                response.json()
            )

        except Exception as e:

            logger.exception(
                "Failed to get response "
                "from Ollama gateway"
            )

            raise RuntimeError(
                "Failed to get response from "
                f"Ollama gateway: {e}"
            ) from e

        logger.debug(
            "Ollama response: %s",
            response_data,
        )

        return (
            self.__prepare_ollama_formatted_output(
                response=response_data,
                model=self._model,
            )
        )

    # ============================================================
    # TOOL RESPONSE → OPENAI FORMAT
    # ============================================================

    @staticmethod
    def convert_tool_response_to_openai_format(
        content
    ) -> list:

        if not content:
            return []

        tool_calls = []

        for index, tool_request in enumerate(
            content
        ):

            if not isinstance(
                tool_request,
                dict,
            ):

                continue

            function = (
                tool_request.get(
                    "function"
                )
                or {}
            )

            if not isinstance(
                function,
                dict,
            ):

                continue

            tool_name = (
                function.get(
                    "name"
                )
            )

            if not tool_name:
                continue

            arguments = (
                function.get(
                    "arguments",
                    {},
                )
            )

            # ----------------------------------------------------
            # Arguments can be dict or JSON string
            # ----------------------------------------------------

            if isinstance(
                arguments,
                str,
            ):

                try:

                    parsed_arguments = (
                        json.loads(
                            arguments
                        )
                    )

                    if isinstance(
                        parsed_arguments,
                        dict,
                    ):

                        arguments = (
                            parsed_arguments
                        )

                    else:

                        arguments = {}

                except (
                    TypeError,
                    ValueError,
                ):

                    logger.warning(
                        "Unable to parse arguments "
                        "for Ollama tool '%s': %s",
                        tool_name,
                        arguments,
                    )

                    arguments = {}

            if not isinstance(
                arguments,
                dict,
            ):

                arguments = {}

            # ----------------------------------------------------
            # Preserve DCD/Ollama tool ID
            # ----------------------------------------------------

            tool_call_id = (
                tool_request.get(
                    "id"
                )
                or (
                    f"call_"
                    f"{uuid.uuid4().hex[:24]}"
                )
            )

            tool_calls.append(
                ChatCompletionMessageToolCall(
                    id=tool_call_id,
                    function={
                        "name": tool_name,
                        "arguments": json.dumps(
                            arguments,
                            ensure_ascii=False,
                        ),
                    },
                    type="function",
                )
            )

        return tool_calls

    # ============================================================
    # JSON RESPONSE NORMALIZATION
    # ============================================================

    @staticmethod
    def __prepare_json_formatted(
        content: str
    ):

        if not isinstance(
            content,
            str,
        ):

            return content

        content = content.strip()

        # --------------------------------------------------------
        # ```json ... ```
        # --------------------------------------------------------

        if "```json" in content:

            pattern = (
                r"```json\s*(.*?)\s*```"
            )

            trim_res = re.findall(
                pattern,
                content,
                re.DOTALL | re.IGNORECASE,
            )

            if trim_res:

                return trim_res[0].strip()

        # --------------------------------------------------------
        # ``` ... ```
        # --------------------------------------------------------

        if (
            content.startswith("```")
            and content.endswith("```")
        ):

            lines = content.splitlines()

            if len(lines) >= 3:

                return "\n".join(
                    lines[1:-1]
                ).strip()

        return content

    # ============================================================
    # OLLAMA RESPONSE → OPENAI RESPONSE
    # ============================================================

    def __prepare_ollama_formatted_output(
        self,
        response,
        model: str
    ) -> ChatCompletion:
        """
        Convert native DCD/Ollama response into
        OpenAI-compatible ChatCompletion.
        """

        logger.debug(
            "Raw Ollama gateway response: %s",
            response,
        )

        # --------------------------------------------------------
        # Validate response
        # --------------------------------------------------------

        if not isinstance(
            response,
            dict,
        ):

            if hasattr(
                response,
                "model_dump",
            ):

                response = (
                    response.model_dump(
                        exclude_none=True
                    )
                )

            elif hasattr(
                response,
                "dict",
            ):

                response = (
                    response.dict()
                )

            else:

                raise TypeError(
                    "Unsupported Ollama response "
                    f"type: {type(response)}"
                )

        # ========================================================
        # Message
        # ========================================================

        response_message = (
            response.get(
                "message"
            )
            or {}
        )

        if not isinstance(
            response_message,
            dict,
        ):

            response_message = {}

        # ========================================================
        # Content
        # ========================================================

        response_content = (
            response_message.get(
                "content"
            )
            or ""
        )

        if response_content:

            response_content = (
                self.__prepare_json_formatted(
                    response_content
                )
            )

        # ========================================================
        # Native tool calls
        # ========================================================

        raw_tool_calls = (
            response_message.get(
                "tool_calls"
            )
            or []
        )

        tool_calls = (
            self.convert_tool_response_to_openai_format(
                raw_tool_calls
            )
        )

        # ========================================================
        # Finish reason
        # ========================================================

        if tool_calls:

            finish_reason = "tool_calls"

            message_content = None

        else:

            finish_reason = "stop"

            message_content = (
                response_content
            )

        # ========================================================
        # Assistant message
        # ========================================================

        message = ChatCompletionMessage(
            role="assistant",
            content=message_content,
            tool_calls=(
                tool_calls
                if tool_calls
                else None
            ),
        )

        # ========================================================
        # Usage
        # ========================================================

        prompt_eval_count = (
            response.get(
                "prompt_eval_count"
            )
            or 0
        )

        eval_count = (
            response.get(
                "eval_count"
            )
            or 0
        )

        total_tokens = (
            prompt_eval_count
            + eval_count
        )

        usage = CompletionUsage(
            prompt_tokens=prompt_eval_count,
            total_tokens=total_tokens,
            completion_tokens=eval_count,
        )

        # ========================================================
        # Response ID
        # ========================================================

        response_id = (
            response.get(
                "id"
            )
            or (
                f"ollama-"
                f"{uuid.uuid4().hex}"
            )
        )

        # ========================================================
        # Created timestamp
        # ========================================================

        created = (
            response.get(
                "created_at"
            )
        )

        if created:

            try:

                from datetime import datetime

                normalized = (
                    str(created)
                    .replace(
                        "Z",
                        "+00:00",
                    )
                )

                created = int(
                    datetime.fromisoformat(
                        normalized
                    ).timestamp()
                )

            except (
                TypeError,
                ValueError,
                OverflowError,
            ):

                created = int(
                    time.time()
                )

        else:

            created = int(
                time.time()
            )

        # ========================================================
        # Final ChatCompletion
        # ========================================================

        return ChatCompletion(
            id=response_id,
            choices=[
                Choice(
                    finish_reason=finish_reason,
                    index=0,
                    message=message,
                )
            ],
            created=created,
            model=(
                response.get(
                    "model"
                )
                or model
            ),
            object="chat.completion",
            usage=usage,
        )

    # ============================================================
    # TOOL JSON
    # ============================================================

    async def get_tool_json(
        self,
        func: Callable
    ) -> dict:

        _func_name = (
            func.__name__
        )

        _doc_str = (
            inspect.getdoc(
                func
            )
            or ""
        )

        _properties = {}

        _type_hints = (
            typing.get_type_hints(
                func
            )
        )

        _signature = (
            inspect.signature(
                func
            )
        )

        _required = []

        async for (
            param,
            param_type
        ) in iter_to_aiter(
            _type_hints.items()
        ):

            if param != "return":

                _type = (
                    await ptype_to_json_scheme(
                        param_type.__name__
                    )
                )

                if _type == "array":

                    if hasattr(
                        param_type,
                        "__args__",
                    ):

                        _properties[
                            param
                        ] = {
                            "type": _type,
                            "description": (
                                f"The "
                                f"{param.replace('_', ' ')}."
                            ),
                            "items": {
                                "type": (
                                    await ptype_to_json_scheme(
                                        param_type.__args__[
                                            0
                                        ].__name__
                                    )
                                )
                            }
                        }

                    else:

                        _properties[
                            param
                        ] = {
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

                    _properties[
                        param
                    ] = {
                        "type": _type,
                        "description": (
                            f"The "
                            f"{param.replace('_', ' ')}."
                        )
                    }

        # --------------------------------------------------------
        # Required parameters
        # --------------------------------------------------------

        for (
            param_name,
            parameter
        ) in _signature.parameters.items():

            if (
                param_name in _properties
                and parameter.default
                is inspect.Parameter.empty
            ):

                _required.append(
                    param_name
                )

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
    # EMBEDDINGS - SYNC
    # ============================================================

    def embed(
        self,
        text: str,
        **kwargs
    ):

        text = text.replace(
            "\n",
            " "
        )

        response = self._sync_client.post(
            "/api/embeddings",
            json={
                "model": self._embed_model,
                "prompt": text,
            },
        )

        self._raise_http_error(
            response
        )

        data = response.json()

        return data.get(
            "embedding"
        )

    # ============================================================
    # EMBEDDINGS - ASYNC
    # ============================================================

    async def aembed(
        self,
        text: str,
        **kwargs
    ):

        text = text.replace(
            "\n",
            " "
        )

        response = (
            await self._async_client.post(
                "/api/embeddings",
                json={
                    "model": self._embed_model,
                    "prompt": text,
                },
            )
        )

        self._raise_http_error(
            response
        )

        data = response.json()

        return data.get(
            "embedding"
        )

    # ============================================================
    # REPLACE INSTANCE VALUES
    # ============================================================

    def __replace_instance_values(
        self,
        source_instance: ChatCompletionParams
    ) -> ChatCompletionParams:

        params = self.kwargs.keys()

        for _key in params:

            if (
                _key
                in source_instance.__fields__
            ):

                setattr(
                    source_instance,
                    _key,
                    self.kwargs[
                        _key
                    ],
                )

        return source_instance

    # ============================================================
    # TOKEN COUNT
    # ============================================================

    def count_tokens(
        self,
        **kwargs
    ):

        return 1

    # ============================================================
    # ACCOUNT TOKENS
    # ============================================================

    async def account_tokens(
        self,
        **kwargs
    ):

        return 1
