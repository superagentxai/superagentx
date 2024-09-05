from typing import Any

from openai import OpenAI, AzureOpenAI, AsyncOpenAI, AsyncAzureOpenAI
from pydantic import BaseModel, Field, conlist, conint
from typing import List, Dict, Union
from openai.types.completion import Completion
from openai.types.chat.chat_completion import ChatCompletion
from agentx.llm.constants import OPENAI_PRICE1K
from agentx.llm.client import Client
from agentx.utils.helper import sync_to_async
import logging
import re
import uuid

logger = logging.getLogger(__name__)
_OPEN_API_BASE_URL_PREFIX = "https://api.openai.com"
_MODEL_KEY_NAME = 'model'
_SEED_KEY_NAME = 'seed'
_CACHE_SEED = 42
_ASSISTANTS_NAME = 'assistants'
_ASSISTANTS_KEY_NAME = 'name'
_ASSISTANTS_KEY_INSTRUCTIONS = 'instructions'
_TOOLS_KEY_NAME = 'tools'


class Message(BaseModel):
    role: str = Field(description='the role of the messenger (either system, user, assistant or tool)',
                      default='system')
    content: str = Field(description='the content of the message (e.g., Write me a '
                                     'beautiful poem)')
    name: str | None = Field(description='Messages can also contain an optional name field, which give the '
                                         'messenger a name', default=None)


class ChatCompletionParams(BaseModel):
    # Required parameters
    model: str | None = Field(description='the name of the model you want to use (e.g., gpt-3.5-turbo, gpt-4, '
                                          'gpt-3.5-turbo-16k-1106)', default=None)
    messages: conlist(Message, min_length=1) = Field(description='the content of the message (e.g., Write me a '
                                                                 'beautiful poem)')

    # Optional parameters
    frequency_penalty: float | None = Field(description='Penalizes tokens based on their frequency, reducing '
                                                        'repetition.', default=None)
    logit_bias: Dict[str, float] | None = Field(description='Modifies likelihood of specified tokens with bias '
                                                            'values.', default=None)
    logprobs: bool | None = Field(description='Returns log probabilities of output tokens if true.', default=False)
    top_logprobs: conint(ge=0) | None = Field(description='Specifies the number of most likely tokens to return at '
                                                          'each position.', default=None)
    max_tokens: int | None = Field(description='Sets the maximum number of generated tokens in chat completion.',
                                   default=None)
    n: int | None = Field(description='Generates a specified number of chat completion choices for each input.',
                          default=1)
    presence_penalty: float | None = Field(description='Penalizes new tokens based on their presence in the text.',
                                           default=0)
    response_format: str | None = Field(description='Specifies the output format, e.g., JSON mode.', default=None)
    seed: int | None = Field(description='Ensures deterministic sampling with a specified seed.',
                             default=None)
    service_tier: str | None = Field(description='Specifies the latency tier to use for processing the request. '
                                                 'This parameter is relevant for customers subscribed to the scale'
                                                 ' tier service:', default=None)
    stop: Union[str, List[str]] | None = Field(description='Specifies up to 4 sequences where the API should stop '
                                                           'generating tokens.', default=None)

    stream: bool | None = Field(description='Sends partial message deltas as tokens become available.',
                                default=False)
    temperature: float | None = Field(description='Sets the sampling temperature between 0 and 2.', default=None)
    top_p: float | None = Field(description='Uses nucleus sampling; considers tokens with top_p probability mass.',
                                default=None)
    tools: List[dict] | None = Field(description='Lists functions the model may call.', default=None)
    tool_choice: str | None = Field(description='Controls the model function calls (none/auto/function).',
                                    default=None)
    user: str = Field(
        description="Unique identifier for end-user monitoring and abuse detection.", default=f'{uuid.uuid4()}')


class OpenAIClient(Client):

    # To set the LLM model

    def __init__(self, client: OpenAI | AsyncOpenAI | AzureOpenAI | AsyncAzureOpenAI):

        self.client = client
        if (
                not isinstance(self.client, OpenAI | AsyncOpenAI | AzureOpenAI | AsyncAzureOpenAI)
                and not str(client.base_url).startswith(_OPEN_API_BASE_URL_PREFIX)
                and not OpenAIClient.is_valid_api_key(self.client.api_key)
        ):
            logger.info(
                "OpenAI or Azure hosted Open AI client, is not valid!"
            )
            super().__init__()

    def chat_completion(self, params: Dict[str, Any] = None) -> ChatCompletion:
        params['model'] = self.client.model  # Get model name from client object attribute and set
        response = self.client.chat.completions.create(**params)
        cost = OpenAIClient.cost(response=response)
        logger.debug(f"Usage Cost : {cost}")
        return self.client.chat.completions.create(**params)

    async def achat_completion(self, params: Dict[str, Any]) -> ChatCompletion:
        params['model'] = self.client.model  # Get model name from client object attribute and set
        response = await self.client.chat.completions.create(**params)
        cost = await sync_to_async(OpenAIClient.cost, response=response)
        logger.debug(f"Usage Cost : {cost}")
        return response

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

    @staticmethod
    def cost(response: Union[ChatCompletion, Completion]) -> float:
        """Calculate the cost of the response."""
        model = response.model
        if model not in OPENAI_PRICE1K:
            # log warning that the model is not found
            logger.warning(
                f'Model {model} is not found. The cost will be 0. In your config_list, add field {{"price" : ['
                f'prompt_price_per_1k, completion_token_price_per_1k]}} for customized pricing.'
            )
            return 0

        n_input_tokens = response.usage.prompt_tokens if response.usage is not None else 0
        n_output_tokens = response.usage.completion_tokens if response.usage is not None else 0
        if n_output_tokens is None:
            n_output_tokens = 0
        tmp_price_1k = OPENAI_PRICE1K[model]
        # First value is input token rate, second value is output token rate
        if isinstance(tmp_price_1k, tuple):
            return (tmp_price_1k[0] * n_input_tokens + tmp_price_1k[1] * n_output_tokens) / 1000
        return tmp_price_1k * (n_input_tokens + n_output_tokens) / 1000
