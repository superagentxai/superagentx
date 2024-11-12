import logging
import json
import pytest

from superagentx.llm import LLMClient, Message
from superagentx.llm.models import ChatCompletionParams
from superagentx.llm.ollama import OllamaClient

logger = logging.getLogger(__name__)

'''
 Run Pytest:

   1. pytest --log-cli-level=INFO tests/llm/test_ollama_client.py::TestOllamaClient::test_ollama_aclient_chat
   2. pytest --log-cli-level=INFO tests/llm/test_ollama_client.py::TestOllamaClient::test_ollama_client_chat
   3. pytest --log-cli-level=INFO tests/llm/test_ollama_client.py::TestOllamaClient::test_ollama_func_client_chat
   4. pytest --log-cli-level=INFO tests/llm/test_ollama_client.py::TestOllamaClient::test_ollama_aclient_embed
   5. pytest --log-cli-level=INFO tests/llm/test_ollama_client.py::TestOllamaClient::test_ollama_client_embed
'''

# Start a conversation with the user message.
user_message = "What is the flight time from New York (NYC) to Los Angeles (LAX)?"

conversations = [
    {
        "role": "user",
        "content": user_message
    }
]

tools = [
    {
        'type': 'function',
        'function': {
            'name': 'get_flight_times',
            'description': 'Get the flight times between two cities',
            'parameters': {
                'type': 'object',
                'properties': {
                    'departure': {
                        'type': 'string',
                        'description': 'The departure city (airport code)',
                    },
                    'arrival': {
                        'type': 'string',
                        'description': 'The arrival city (airport code)',
                    },
                },
                'required': ['departure', 'arrival'],
            },
        },
    },
]


@pytest.fixture
def ollama_client_init() -> dict:
    # llm_config = {'model': 'anthropic.claude-3-5-sonnet-20240620-v1:0', 'llm_type': 'bedrock'}
    llm_config = {'model': 'mistral', 'llm_type': 'ollama', 'async_mode': True}
    llm_client: LLMClient = LLMClient(llm_config=llm_config)
    response = {'llm': llm_client}
    return response


class TestOllamaClient:

    async def test_bedrock_client_init(self, ollama_client_init: dict):
        llm_client: LLMClient = ollama_client_init.get('llm').client
        assert isinstance(llm_client, OllamaClient)

    async def test_ollama_aclient_chat(self, ollama_client_init: dict):
        llm_client: LLMClient = ollama_client_init.get('llm')

        chat_completion_params = ChatCompletionParams(
            messages=conversations,
            tools=tools
        )

        response = await llm_client.achat_completion(chat_completion_params=chat_completion_params)
        logger.info(response)

    async def test_ollama_client_chat(self, ollama_client_init: dict):
        llm_client: LLMClient = ollama_client_init.get('llm')

        chat_completion_params = ChatCompletionParams(
            messages=conversations,
            tools=tools
        )

        response = llm_client.chat_completion(chat_completion_params=chat_completion_params)
        logger.info(response)

    #
    async def test_ollama_func_client_chat(self, ollama_client_init: dict):
        llm_client: LLMClient = ollama_client_init.get('llm')

        chat_completion_params = ChatCompletionParams(
            messages=conversations,
            tools=tools
        )

        result: [Message] = await llm_client.afunc_chat_completion(chat_completion_params=chat_completion_params)
        logger.info(f'Result {result}')

    async def test_ollama_aclient_embed(self, ollama_client_init: dict):
        llm_client: LLMClient = ollama_client_init.get('llm')

        response = await llm_client.aembed(text="Hi")
        logger.info(response)

    async def test_ollama_client_embed(self, ollama_client_init: dict):
        llm_client: LLMClient = ollama_client_init.get('llm')

        response = llm_client.embed(text="Hi")
        logger.info(response)
