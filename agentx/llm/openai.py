import logging
import re

from openai import OpenAI, AzureOpenAI, AsyncOpenAI, AsyncAzureOpenAI
from openai.types.chat.chat_completion import ChatCompletion
from openai.types.completion import Completion

from agentx.llm import ChatCompletionParams
from agentx.llm.client import Client
from agentx.llm.constants import OPENAI_PRICE1K
from agentx.utils.helper import sync_to_async

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
            client: OpenAI | AsyncOpenAI | AzureOpenAI | AsyncAzureOpenAI
    ):

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

    def chat_completion(
            self,
            *,
            chat_completion_params: ChatCompletionParams
    ) -> ChatCompletion:
        params = chat_completion_params.model_dump(exclude_none=True)
        params['model'] = getattr(self.client, 'model')  # Get model name from client object attribute and set
        response = self.client.chat.completions.create(**params)
        cost = OpenAIClient.cost(response=response)
        logger.debug(f"Usage Cost : {cost}")
        return self.client.chat.completions.create(**params)

    async def achat_completion(
            self,
            *,
            chat_completion_params: ChatCompletionParams
    ) -> ChatCompletion:
        params = chat_completion_params.model_dump(exclude_none=True)
        params['model'] = getattr(self.client, 'model')  # Get model name from client object attribute and set
        response = await self.client.chat.completions.create(**params)
        cost = await sync_to_async(
            OpenAIClient.cost,
            response=response
        )
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
    def cost(response: ChatCompletion | Completion) -> float:
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
