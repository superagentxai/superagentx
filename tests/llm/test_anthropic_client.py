import logging

import pytest

from superagentx.llm import LLMClient, Message
from superagentx.llm.openai import OpenAIClient
from superagentx.llm.models import ChatCompletionParams

logger = logging.getLogger(__name__)

'''
Run Pytest:  

    1. pytest --log-cli-level=INFO tests/llm/test_anthropic_client.py::TestAnthropicClient::test_anthropic_client_init
    2. pytest --log-cli-level=INFO tests/llm/test_anthropic_client.py::TestAnthropicClient::test_anthropic_aclient_converse
    3. pytest --log-cli-level=INFO tests/llm/test_anthropic_client.py::TestAnthropicClient::test_anthropic_client_converse
    4. pytest --log-cli-level=INFO tests/llm/test_anthropic_client.py::TestAnthropicClient::test_anthropic_func_client_converse
    5. pytest --log-cli-level=INFO tests/llm/test_anthropic_client.py::TestAnthropicClient::test_anthropic_aclient_embed
    6. pytest --log-cli-level=INFO tests/llm/test_anthropic_client.py::TestAnthropicClient::test_anthropic_client_embed
'''

# Start a conversation with the user message.
user_message = "What is the most famous song on ABCD?"

conversations = [
            {
                "role": "user",
                "content": user_message
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


@pytest.fixture
def anthropic_client_init() -> dict:
    # llm_config = {'model': 'anthropic.claude-3-5-sonnet-20240620-v1:0', 'llm_type': 'anthropic'}
    llm_config = {
        'model': 'claude-3-7-sonnet-20250219',
        'llm_type': 'anthropic',
        'async_mode': True
    }
    llm_client: LLMClient = LLMClient(llm_config=llm_config)
    response = {'llm': llm_client}
    return response


class TestAnthropicClient:

    async def test_anthropic_client_init(self, anthropic_client_init: dict):
        llm_client: LLMClient = anthropic_client_init.get('llm').client
        assert isinstance(llm_client, OpenAIClient)

    async def test_message_format(self):
        formatted_messages = []
        message = {}

        for conversation in conversations:

            if conversation.get('role') == 'user':
                message['role'] = 'user'
                message['content'] = [conversation.get('content')]
                formatted_messages.append(message)
            else:
                formatted_messages.append(conversation)

        logger.info(f'Messages {formatted_messages}')

    async def test_anthropic_aclient_converse(self, anthropic_client_init: dict):
        llm_client: LLMClient = anthropic_client_init.get('llm')

        chat_completion_params = ChatCompletionParams(
            messages=conversations,
            tools=tools
        )

        response = await llm_client.achat_completion(chat_completion_params=chat_completion_params)
        logger.info(response)

    async def test_anthropic_client_converse(self, anthropic_client_init: dict):
        llm_client: LLMClient = anthropic_client_init.get('llm')

        chat_completion_params = ChatCompletionParams(
            messages=conversations,
            tools=tools
        )

        response = llm_client.chat_completion(chat_completion_params=chat_completion_params)
        logger.info(response)

    async def test_anthropic_func_client_converse(self, anthropic_client_init: dict):
        llm_client: LLMClient = anthropic_client_init.get('llm')

        chat_completion_params = ChatCompletionParams(
            messages=conversations,
            tools=tools
        )

        result: [Message] = await llm_client.afunc_chat_completion(chat_completion_params=chat_completion_params)
        logger.info(f'Result {result}')

    async def test_anthropic_aclient_embed(self, anthropic_client_init: dict):
        llm_client: LLMClient = anthropic_client_init.get('llm')

        response = await llm_client.aembed(text="Hi")
        logger.info(response)

    async def test_anthropic_client_embed(self, anthropic_client_init: dict):
        llm_client: LLMClient = anthropic_client_init.get('llm')

        response = llm_client.embed(text="Hi")
        logger.info(response)