import logging

import pytest

from superagentx.llm import LLMClient, Message, ChatCompletionParams
from superagentx.llm.litellm import LiteLLMClient
from openai.types.chat.chat_completion import ChatCompletion

logger = logging.getLogger(__name__)


@pytest.fixture
def litellm_client_init() -> dict:
    # llm_config = {'model': 'DFGPT4o', 'llm_type': 'azure-openai'}
    llm_config = {'model': 'openai/gpt-5-mini'}
    # llm_config = {'model': 'anthropic/claude-sonnet-4-5-20250929'}
    llm_client: LLMClient = LLMClient(llm_config=llm_config)
    response = {'llm': llm_client, 'llm_type': 'openai'}
    return response


class TestLiteLLMClient:
    async def test_litellm_client(self, litellm_client_init: dict):
        llm_client: LLMClient = litellm_client_init.get('llm').client
        assert isinstance(llm_client, LiteLLMClient)

    async def test_chat_completion(self, litellm_client_init: dict):
        llm_client: LLMClient = litellm_client_init.get('llm')
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user",
                "content": "Hi, My order id is 3454232.can you tell me the delivery date for my order?!."
            }
        ]

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_delivery_date",
                    "description": "Get the delivery date for a customer's order. Call this whenever you need to know "
                                   "the"
                                   "delivery date, for example when a customer asks 'Where is my package'",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "order_id": {
                                "type": "string",
                                "description": "The customer's order ID.",
                            },
                        },
                        "required": ["order_id"],
                        "additionalProperties": False,
                    },
                }
            }
        ]

        chat_completion_params = ChatCompletionParams(
            messages=messages,
            tools=tools,
            stream=False
        )

        response: ChatCompletion = llm_client.chat_completion(chat_completion_params=chat_completion_params)
        logger.info(f"Chat Response {response}")

        # for part in response:
        #     logger.info(part)
