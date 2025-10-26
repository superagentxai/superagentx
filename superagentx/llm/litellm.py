import inspect
import logging
import re
from pydantic import typing

from openai.types.chat.chat_completion import ChatCompletion, Choice, ChoiceLogprobs
from openai.types.chat.chat_completion_message import ChatCompletionMessage
from openai.types.completion_usage import CompletionUsage
from litellm import completion, acompletion, embedding, aembedding, ModelResponse
from openai.types.chat.chat_completion import ChatCompletion
from superagentx.llm.models import ChatCompletionParams
from superagentx.llm.client import Client
from superagentx.utils.helper import sync_to_async, iter_to_aiter, ptype_to_json_scheme

logger = logging.getLogger(__name__)


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

    # Ensure ModelResponse has choices and model attributes
    if not hasattr(model_response, "choices"):
        raise ValueError("Invalid ModelResponse: missing 'choices' field")
    if not hasattr(model_response, "model"):
        raise ValueError("Invalid ModelResponse: missing 'model' field")

    converted_choices: list[Choice] = []

    for idx, choice in enumerate(model_response.choices):
        # Determine message content
        message_content = None
        finish_reason = getattr(choice, "finish_reason", "stop")

        # Some models might have 'message' dict or 'delta' (streamed output)
        if hasattr(choice, "message") and choice.message:
            msg_data = choice.message
            if isinstance(msg_data, dict):
                message_content = ChatCompletionMessage(**msg_data)
            else:
                # Assume BaseModel
                message_content = ChatCompletionMessage(**msg_data.model_dump())
        elif hasattr(choice, "delta") and choice.delta:
            # Streaming partials
            delta = choice.delta
            if isinstance(delta, dict):
                message_content = ChatCompletionMessage(**delta)
            else:
                message_content = ChatCompletionMessage(**delta.model_dump())
        else:
            message_content = ChatCompletionMessage(role="assistant", content="")

        # Handle optional logprobs
        logprobs = getattr(choice, "logprobs", None)
        if logprobs and isinstance(logprobs, dict):
            logprobs = ChoiceLogprobs(**logprobs)
        elif logprobs is None:
            logprobs = None

        converted_choices.append(
            Choice(
                index=idx,
                message=message_content,
                finish_reason=finish_reason or "stop",
                logprobs=logprobs,
            )
        )

    # Convert usage if present
    usage = None
    if hasattr(model_response, "usage") and model_response.usage:
        usage_data = model_response.usage
        if isinstance(usage_data, dict):
            usage = CompletionUsage(**usage_data)
        else:
            usage = CompletionUsage(**usage_data.model_dump())

    chat_completion = ChatCompletion(
        id=getattr(model_response, "id", "unknown"),
        choices=converted_choices,
        created=getattr(model_response, "created", 0),
        model=getattr(model_response, "model", "unknown"),
        object="chat.completion",
        system_fingerprint=getattr(model_response, "system_fingerprint", None),
        usage=usage,
    )

    return chat_completion


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

        # LiteLLM unified interface
        response = completion(**params)
        chat_completion_response: ChatCompletion = convert_model_response_to_chat_completion(model_response=response)

        return chat_completion_response

    async def achat_completion(
            self,
            *,
            chat_completion_params: ChatCompletionParams,
    ):
        """Asynchronous chat completion"""
        params = chat_completion_params.model_dump(exclude_none=True)
        params["model"] = self._model
        response = await acompletion(**params)
        chat_completion_response: ChatCompletion = await sync_to_async(convert_model_response_to_chat_completion,
                                                                       model_response=response)
        return chat_completion_response

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

    def embed(self, text: str, **kwargs):
        pass

    async def aembed(self, text: str, **kwargs):
        pass

    def count_tokens(self, chat_completion_params: ChatCompletionParams):
        import tiktoken
        """
        Count tokens for OpenAI chat messages.
        """
        try:
            encoding = tiktoken.encoding_for_model(self._model)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")

        tokens_per_message = 3
        tokens_per_name = 1
        num_tokens = 0

        for message in chat_completion_params.messages:
            num_tokens += tokens_per_message
            num_tokens += len(encoding.encode(message.content))
        num_tokens += 3  # every reply is primed with <|start|>assistant
        return num_tokens

    async def acount_tokens(self, chat_completion_params: ChatCompletionParams):
        return await sync_to_async(self.count_tokens, chat_completion_params)
