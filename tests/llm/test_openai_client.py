import logging

import pytest
from openai.types.chat.chat_completion import ChatCompletion

from agentx.llm import LLMClient
from agentx.llm.openai import ChatCompletionParams
from agentx.llm.openai import OpenAIClient

logger = logging.getLogger(__name__)

'''
 Run Pytest:  
    
   1. pytest --log-cli-level=INFO tests/llm/test_openai_client.py::TestOpenAIClient::test_achat_completion
   2. pytest --log-cli-level=INFO tests/llm/test_openai_client.py::TestOpenAIClient::test_chat_completion
'''


@pytest.fixture
def openai_client_init() -> dict:
    llm_config = {'model': 'gpt-4-turbo-2024-04-09', 'llm_type': 'openai', 'async_mode': False}

    llm_client: LLMClient = LLMClient(model='openai', llm_config=llm_config)
    response = {'llm': llm_client, 'llm_type': 'openai'}
    return response


class TestOpenAIClient:

    async def test_openai_client(self, openai_client_init: dict):
        llm_client: LLMClient = openai_client_init.get('llm')
        assert isinstance(llm_client, OpenAIClient)

    async def test_chat_completion(self, openai_client_init: dict):
        llm_client: LLMClient = openai_client_init.get('llm')
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

        params = ChatCompletionParams(
            # model='gpt-3.5-turbo',
            messages=messages,
            seed=34,
            tools=tools,
        ).model_dump(exclude_none=True)

        response = llm_client.chat_completion(params=params)
        logger.info(f"Open AI ChatCompletion Response {response}")
        assert isinstance(response, ChatCompletion)
        assert isinstance(openai_client_init.get('llm'), LLMClient)

    async def test_achat_completion(self, openai_client_init: dict):
        llm_client: LLMClient = openai_client_init.get('llm')

        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user",
                "content": "Hi, Tell me about Agentic Framework"
            }
        ]

        params = ChatCompletionParams(
            messages=messages,
        ).model_dump(exclude_none=True)
        response = await llm_client.achat_completion(params=params)
        logger.info(f"Open AI Async ChatCompletion Response {response}")
        assert isinstance(response, ChatCompletion)
