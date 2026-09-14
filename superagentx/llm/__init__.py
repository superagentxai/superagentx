import json
import logging
import os
from datetime import datetime, timezone
from typing import List, Callable

from openai import OpenAI, AzureOpenAI, AsyncOpenAI, AsyncAzureOpenAI
from openai.types.chat import ChatCompletion

from superagentx.exceptions import InvalidType
from superagentx.llm.constants import (
    DEFAULT_OPENAI_EMBED,
    DEFAULT_BEDROCK_EMBED,
    DEFAULT_OLLAMA_EMBED,
    DEFAULT_EMBED,
    DEFAULT_GEMINI_EMBED,
)
from superagentx.llm.litellm import LiteLLMClient
from superagentx.llm.models import ChatCompletionParams
from superagentx.llm.openai import OpenAIClient
from superagentx.llm.types.base import LLMModelConfig
from superagentx.llm.types.response import Message, Tool
from superagentx.utils.helper import iter_to_aiter, sync_to_async
from superagentx.utils.llm_config import LLMType


logger = logging.getLogger(__name__)


_retries = 5

_deepseek_base_url = "https://api.deepseek.com"
_anthropic_base_url = "https://api.anthropic.com/v1/"
_routeway_base_url = "https://api.routeway.ai/v1"


class LLMClient:
    """
    Base LLM Client to create LLM client based on model llm_type.

    Supported model types include:

        openai
        azure-openai
        deepseek
        anthropic
        routeway
        bedrock
        gemini
        ollama
        custom
        litellm
    """

    def __init__(
        self,
        *,
        llm_config: dict,
        **kwargs
    ):
        self.llm_config = llm_config

        self.llm_config_model = LLMModelConfig(
            **self.llm_config
        )

        self.async_mode = self.llm_config_model.async_mode

        # ---------------------------------------------------------
        # Select LLM implementation
        # ---------------------------------------------------------

        match self.llm_config_model.llm_type:

            case (
                LLMType.OPENAI_CLIENT
                | LLMType.ANTHROPIC_CLIENT
                | LLMType.DEEPSEEK
                | LLMType.ROUTEWAY
                | LLMType.CUSTOM
            ):
                self.client = self._init_openai_cli()

            case LLMType.AZURE_OPENAI_CLIENT:
                self.client = self._init_azure_openai_cli()

            case LLMType.BEDROCK_CLIENT:
                self.client = self._init_bedrock_cli(
                    **kwargs
                )

            case LLMType.GEMINI_CLIENT:
                self.client = self._init_gemini_cli(
                    **kwargs
                )

            case LLMType.OLLAMA:
                self.client = self._init_ollama_cli(
                    **kwargs
                )

            case _:
                # Preserve existing LiteLLM fallback
                self.client = self.__init_litellm_cli()

    # ============================================================
    # OPENAI / CUSTOM / DEEPSEEK / ANTHROPIC / ROUTEWAY
    # ============================================================

    def _init_openai_cli(self) -> OpenAIClient:

        llm_type = self.llm_config_model.llm_type

        # ---------------------------------------------------------
        # CUSTOM LLM
        #
        # Custom LLM does NOT use the OpenAI SDK.
        #
        # OpenAIClient will use aiohttp and call:
        #
        #     {base_url}/api/chat
        #
        # Credentials can come from:
        #
        #     llm_config
        #
        # or ENV:
        #
        #     CUSTOM_LLM_BASE_URL
        #     CUSTOM_LLM_API_KEY
        #     CUSTOM_LLM_CLIENT_SECRET
        # ---------------------------------------------------------

        if llm_type == LLMType.CUSTOM:

            base_url = (
                self.llm_config_model.base_url
                or os.getenv("CUSTOM_LLM_BASE_URL")
            )

            api_key = (
                self.llm_config_model.api_key
                or os.getenv("CUSTOM_LLM_API_KEY")
            )

            client_secret = (
                getattr(
                    self.llm_config_model,
                    "client_secret",
                    None
                )
                or os.getenv("CUSTOM_LLM_CLIENT_SECRET")
            )

            if not base_url:
                raise ValueError(
                    "Custom LLM base_url is required. "
                    "Set 'base_url' in llm_config or "
                    "CUSTOM_LLM_BASE_URL environment variable."
                )

            if not api_key:
                raise ValueError(
                    "Custom LLM api_key is required. "
                    "Set 'api_key' in llm_config or "
                    "CUSTOM_LLM_API_KEY environment variable."
                )

            if not client_secret:
                raise ValueError(
                    "Custom LLM client_secret is required. "
                    "Set 'client_secret' in llm_config or "
                    "CUSTOM_LLM_CLIENT_SECRET environment variable."
                )

            embed_model = (
                self.llm_config_model.embed_model
            )

            return OpenAIClient(
                client=None,
                model=self.llm_config_model.model,
                embed_model=(
                    embed_model
                    or DEFAULT_OPENAI_EMBED
                ),
                llm_type=LLMType.CUSTOM,
                base_url=base_url,
                api_key=api_key,
                client_secret=client_secret,
            )

        # ---------------------------------------------------------
        # Existing OpenAI-compatible providers
        # ---------------------------------------------------------

        client_class = (
            AsyncOpenAI
            if self.llm_config_model.async_mode
            else OpenAI
        )

        base_url = None
        api_key = None

        # ---------------------------------------------------------
        # Anthropic
        # ---------------------------------------------------------

        if llm_type == LLMType.ANTHROPIC_CLIENT:

            base_url = (
                self.llm_config_model.base_url
                or _anthropic_base_url
            )

            api_key = (
                self.llm_config_model.api_key
                or os.getenv("ANTHROPIC_API_KEY")
            )

        # ---------------------------------------------------------
        # DeepSeek
        # ---------------------------------------------------------

        if llm_type == LLMType.DEEPSEEK:

            base_url = (
                self.llm_config_model.base_url
                or _deepseek_base_url
            )

            api_key = (
                self.llm_config_model.api_key
                or os.getenv("DEEPSEEK_API_KEY")
            )

        # ---------------------------------------------------------
        # Routeway
        # ---------------------------------------------------------

        if llm_type == LLMType.ROUTEWAY:

            base_url = (
                self.llm_config_model.base_url
                or _routeway_base_url
            )

            api_key = (
                self.llm_config_model.api_key
                or os.getenv("Routeway_API_KEY")
            )

        # ---------------------------------------------------------
        # OpenAI
        # ---------------------------------------------------------

        if llm_type == LLMType.OPENAI_CLIENT:

            api_key = (
                self.llm_config_model.api_key
                or os.getenv("OPENAI_API_KEY")
            )

        # ---------------------------------------------------------
        # Initialize OpenAI SDK
        # ---------------------------------------------------------

        cli = client_class(
            api_key=api_key,
            base_url=base_url or None,
        )

        embed_model = (
            self.llm_config_model.embed_model
        )

        return OpenAIClient(
            client=cli,
            model=self.llm_config_model.model,
            embed_model=(
                embed_model
                or DEFAULT_OPENAI_EMBED
            ),
            llm_type=llm_type,
        )

    # ============================================================
    # LITELLM
    # ============================================================

    def __init_litellm_cli(self):

        return LiteLLMClient(
            model=self.llm_config_model.model
        )

    # ============================================================
    # GEMINI
    # ============================================================

    def _init_gemini_cli(
        self,
        **kwargs
    ):

        from superagentx.llm.gemini import GeminiClient

        api_key = (
            self.llm_config_model.api_key
            or os.getenv("GEMINI_API_KEY")
        )

        from google import genai

        cli = genai.Client(
            api_key=api_key
        )

        embed_model = (
            self.llm_config_model.embed_model
        )

        return GeminiClient(
            client=cli,
            model=self.llm_config_model.model,
            embed_model=(
                embed_model
                or DEFAULT_GEMINI_EMBED
            ),
        )

    # ============================================================
    # AZURE OPENAI
    # ============================================================

    def _init_azure_openai_cli(
        self
    ) -> OpenAIClient:

        api_key = (
            self.llm_config_model.api_key
            or os.getenv("AZURE_OPENAI_API_KEY")
            or os.getenv("AZURE_API_KEY")
        )

        base_url = (
            self.llm_config_model.base_url
            or os.getenv("AZURE_ENDPOINT")
            or os.getenv("AZURE_API_BASE")
        )

        azure_deployment = (
            self.llm_config_model.model
            or os.getenv("AZURE_DEPLOYMENT")
        )

        api_version = (
            self.llm_config_model.api_version
            or os.getenv("API_VERSION")
            or os.getenv("AZURE_API_VERSION")
        )

        client_class = (
            AsyncAzureOpenAI
            if self.llm_config_model.async_mode
            else AzureOpenAI
        )

        cli = client_class(
            api_key=api_key,
            azure_endpoint=base_url,
            api_version=api_version,
        )

        return OpenAIClient(
            client=cli,
            model=azure_deployment,
            embed_model=self.llm_config_model.embed_model,
            llm_type=LLMType.AZURE_OPENAI_CLIENT,
        )

    # ============================================================
    # BEDROCK
    # ============================================================

    def _init_bedrock_cli(
        self,
        **kwargs
    ):

        import boto3
        from botocore.config import Config
        from superagentx.llm.bedrock import BedrockClient

        aws_region = (
            kwargs.get("aws_region", None)
            or os.getenv("AWS_REGION")
            or os.getenv("AWS_REGION_NAME")
        )

        if not aws_region:
            raise ValueError(
                "Region is required to use the Amazon Bedrock API."
            )

        aws_access_key = (
            kwargs.get("aws_access_key", None)
            or os.getenv("AWS_ACCESS_KEY")
            or os.getenv("AWS_ACCESS_KEY_ID")
        )

        aws_secret_key = (
            kwargs.get("aws_secret_key", None)
            or os.getenv("AWS_SECRET_KEY")
            or os.getenv("AWS_SECRET_ACCESS_KEY")
        )

        bedrock_config = Config(
            region_name=aws_region,
            signature_version="v4",
            retries={
                "max_attempts": _retries,
                "mode": "standard",
            },
        )

        aws_cli = boto3.client(
            service_name="bedrock-runtime",
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            config=bedrock_config,
        )

        embed_model = (
            self.llm_config_model.embed_model
        )

        return BedrockClient(
            client=aws_cli,
            model=self.llm_config_model.model,
            embed_model=(
                DEFAULT_BEDROCK_EMBED
                if not embed_model
                else embed_model
            ),
        )

    # ============================================================
    # OLLAMA
    # ============================================================

    def _init_ollama_cli(
        self,
        **kwargs
    ):

        from ollama import AsyncClient
        from ollama import Client as OllamaCli
        from superagentx.llm.ollama import OllamaClient

        host = (
            kwargs.get("host", None)
            or os.getenv("OLLAMA_HOST")
        )

        cli = (
            AsyncClient(host=host)
            if self.llm_config_model.async_mode
            else OllamaCli(host=host)
        )

        embed_model = (
            self.llm_config_model.embed_model
        )

        return OllamaClient(
            client=cli,
            embed_model=(
                DEFAULT_OLLAMA_EMBED
                if not embed_model
                else embed_model
            ),
            model=self.llm_config_model.model,
            **kwargs
        )

    # ============================================================
    # CHAT COMPLETION
    # ============================================================

    def chat_completion(
        self,
        *,
        chat_completion_params: ChatCompletionParams
    ) -> ChatCompletion:

        return self.client.chat_completion(
            chat_completion_params=chat_completion_params
        )

    # ============================================================
    # ASYNC CHAT COMPLETION
    # ============================================================

    async def achat_completion(
        self,
        *,
        chat_completion_params: ChatCompletionParams
    ) -> ChatCompletion:

        if self.async_mode:

            return await self.client.achat_completion(
                chat_completion_params=chat_completion_params
            )

        return await sync_to_async(
            self.client.chat_completion,
            chat_completion_params=chat_completion_params
        )

    # ============================================================
    # TOOL JSON
    # ============================================================

    async def get_tool_json(
        self,
        *,
        func: Callable
    ) -> dict:

        return await self.client.get_tool_json(
            func=func
        )

    # ============================================================
    # EMBED
    # ============================================================

    def embed(
        self,
        *,
        text: str,
        **kwargs
    ):

        return self.client.embed(
            text,
            **kwargs
        )

    # ============================================================
    # ASYNC EMBED
    # ============================================================

    async def aembed(
        self,
        *,
        text: str,
        **kwargs
    ):

        if self.async_mode:

            return await self.client.aembed(
                text,
                **kwargs
            )

        return await sync_to_async(
            self.client.embed,
            text,
            **kwargs
        )

    # ============================================================
    # FUNCTION / TOOL CHAT COMPLETION
    # ============================================================

    async def afunc_chat_completion(
        self,
        *,
        chat_completion_params: ChatCompletionParams
    ) -> List[Message]:

        stream = bool(
            chat_completion_params.stream
        )

        # Most models don't support streaming with tool use
        if stream:

            logger.warning(
                "Streaming is not currently supported, "
                "streaming will be disabled."
            )

            chat_completion_params.stream = False

        if self.async_mode:

            response: ChatCompletion = (
                await self.client.achat_completion(
                    chat_completion_params=chat_completion_params
                )
            )

        else:

            response: ChatCompletion = await sync_to_async(
                self.client.chat_completion,
                chat_completion_params=chat_completion_params
            )

        message_instances = []

        if response:

            async for choice in iter_to_aiter(
                response.choices
            ):

                tool_calls_data = []

                if choice.message.tool_calls:

                    tool_calls_data = [
                        Tool(
                            tool_type=tool_call.type,
                            name=tool_call.function.name,
                            arguments=json.loads(
                                tool_call.function.arguments
                            )
                        )
                        async for tool_call
                        in iter_to_aiter(
                            choice.message.tool_calls
                        )
                    ]

                usage_data = response.usage

                msg = choice.message
                usage = usage_data

                details = getattr(
                    usage,
                    "completion_tokens_details",
                    None
                )

                message_instances.append(
                    Message(
                        role=msg.role,
                        model=response.model,
                        content=msg.content,
                        tool_calls=(
                            tool_calls_data
                            or None
                        ),
                        completion_tokens=(
                            usage.completion_tokens
                            if usage
                            else 0
                        ),
                        prompt_tokens=(
                            usage.prompt_tokens
                            if usage
                            else 0
                        ),
                        total_tokens=(
                            usage.total_tokens
                            if usage
                            else 0
                        ),
                        reasoning_tokens=(
                            details.reasoning_tokens
                            if details
                            and hasattr(
                                details,
                                "reasoning_tokens"
                            )
                            else 0
                        ),
                        created=datetime.fromtimestamp(
                            response.created,
                            tz=timezone.utc
                        )
                    )
                )

        return message_instances

    # ============================================================
    # TOKEN COUNT
    # ============================================================

    def count_tokens(
        self,
        chat_completion_params: ChatCompletionParams
    ):

        return self.client.count_tokens(
            chat_completion_params=chat_completion_params
        )

    # ============================================================
    # ACCOUNT TOKENS
    # ============================================================

    async def account_tokens(
        self,
        chat_completion_params: ChatCompletionParams
    ):

        if self.async_mode:

            return await self.client.account_tokens(
                chat_completion_params=chat_completion_params
            )

        return await sync_to_async(
            self.count_tokens,
            chat_completion_params
        )