import inspect
import logging
import typing
import warnings
from typing import Callable

from openai.types.chat.chat_completion import ChatCompletion, Choice, ChoiceLogprobs
from openai.types.chat.chat_completion_message import ChatCompletionMessage
from openai.types.completion_usage import CompletionUsage
from litellm import completion, acompletion, embedding, aembedding, ModelResponse
from superagentx.llm.models import ChatCompletionParams
from superagentx.llm.client import Client
from superagentx.utils.helper import sync_to_async, ptype_to_json_scheme

logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore", category=UserWarning, message=".*Pydantic serializer warnings.*")



def _to_chat_message(obj) -> ChatCompletionMessage:
    """Convert dict/BaseModel-like object to ChatCompletionMessage."""
    if isinstance(obj, dict):
        return ChatCompletionMessage(**obj)
    if hasattr(obj, "model_dump"):
        return ChatCompletionMessage(**obj.model_dump())
    raise ValueError(f"Unsupported message type: {type(obj)}")


def convert_model_response_to_chat_completion(
    model_response: ModelResponse,
) -> ChatCompletion:
    """
        Convert a custom ModelResponse object into a standard OpenAI ChatCompletion object.

        Args:
            model_response (ModelResponse): The source model response object.

        Returns:
            ChatCompletion: Converted ChatCompletion instance.
        """
    if not hasattr(model_response, "choices") or not hasattr(model_response, "model"):
        raise ValueError(
            "Invalid ModelResponse: missing required fields ('choices', 'model')"
        )

    converted_choices: list[Choice] = []

    for idx, choice in enumerate(model_response.choices):
        msg = getattr(choice, "message", None) or getattr(choice, "delta", None)
        message = _to_chat_message(msg)

        logprobs = getattr(choice, "logprobs", None)
        if isinstance(logprobs, dict):
            logprobs = ChoiceLogprobs(**logprobs)

        converted_choices.append(
            Choice(
                index=idx,
                message=message,
                finish_reason=getattr(choice, "finish_reason", None) or "stop",
                logprobs=logprobs,
            )
        )

    usage = None
    usage_data = getattr(model_response, "usage", None)
    if usage_data:
        if isinstance(usage_data, dict):
            usage = CompletionUsage(**usage_data)
        elif hasattr(usage_data, "model_dump"):
            usage = CompletionUsage(
                **usage_data.model_dump(
                    mode="json",
                    exclude_none=True,
                )
            )

    return ChatCompletion(
        id=getattr(model_response, "id", "unknown"),
        object="chat.completion",
        created=getattr(model_response, "created", 0),
        model=model_response.model,
        choices=converted_choices,
        usage=usage,
        system_fingerprint=getattr(model_response, "system_fingerprint", None),
    )


class LiteLLMClient(Client):
    """
    LiteLLM-based implementation for chat, embedding, and token-cost calculation.
    Compatible with OpenAI, Anthropic, Gemini, Claude, etc.
    """

    def chat_completion(
        self,
        *,
        chat_completion_params: ChatCompletionParams,
    ) -> ChatCompletion:
        """Synchronous chat completion"""
        params = chat_completion_params.model_dump(exclude_none=True)
        params["model"] = self._model
        params["stream"] = False  # Streaming not yet supported

        response: ModelResponse = completion(**params)
        logger.debug(
            f"LiteLLM sync completion: model={response.model}, "
            f"choices={len(response.choices)}, usage={getattr(response, 'usage', None)}"
        )

        return convert_model_response_to_chat_completion(model_response=response)

    async def achat_completion(
        self,
        *,
        chat_completion_params: ChatCompletionParams,
    ) -> ChatCompletion:
        """Asynchronous chat completion"""
        params = chat_completion_params.model_dump(exclude_none=True)
        params["model"] = self._model
        params["stream"] = False  # Streaming not yet supported

        response = await acompletion(**params)

        logger.debug(
            f"LiteLLM async completion: model={response.model}, "
            f"choices={len(response.choices)}, usage={getattr(response, 'usage', None)}"
        )

        return await sync_to_async(convert_model_response_to_chat_completion, model_response=response)

    async def get_tool_json(self, func: Callable) -> dict:
        """
        Generate a JSON schema definition for a callable function for LLM tool use.
        """
        func_name = func.__name__
        doc_str = inspect.getdoc(func)
        properties: dict[str, dict] = {}
        type_hints = typing.get_type_hints(func)

        for param, param_type in type_hints.items():
            if param == "return":
                continue

            type_name = await ptype_to_json_scheme(param_type.__name__)
            if type_name == "array":
                item_type = (
                    await ptype_to_json_scheme(param_type.__args__[0].__name__)
                    if hasattr(param_type, "__args__")
                    else "object"
                )
                properties[param] = {
                    "type": "array",
                    "description": f"The {param.replace('_', ' ')}.",
                    "items": {"type": item_type},
                }
            else:
                properties[param] = {
                    "type": type_name,
                    "description": f"The {param.replace('_', ' ')}.",
                }

        return {
            "type": "function",
            "function": {
                "name": func_name,
                "description": doc_str,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": list(properties.keys()),
                },
            },
        }

    def embed(self, text: str, **kwargs):
        """Synchronous embedding"""
        return embedding(model=self._embed_model, input=[text])

    async def aembed(self, text: str, **kwargs):
        """Asynchronous embedding"""
        return await aembedding(model=self._embed_model, input=[text])

    def count_tokens(self, chat_completion_params: ChatCompletionParams):
        """
        Count tokens for OpenAI-style chat messages.
        """
        import tiktoken

        try:
            encoding = tiktoken.encoding_for_model(self._model)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")

        tokens_per_message = 3
        num_tokens = 0

        for message in chat_completion_params.messages:
            num_tokens += tokens_per_message
            content = message.content
            if isinstance(content, str):
                num_tokens += len(encoding.encode(content))
            elif isinstance(content, dict):
                num_tokens += len(encoding.encode(str(content)))

        num_tokens += 3  # every reply is primed with <|start|>assistant
        return num_tokens

    async def account_tokens(self, chat_completion_params: ChatCompletionParams):
        """Asynchronous token counter"""
        return await sync_to_async(self.count_tokens, chat_completion_params)
