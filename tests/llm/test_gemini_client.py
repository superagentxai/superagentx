import logging
import pytest

from superagentx.llm import LLMClient
from superagentx.llm.models import ChatCompletionParams
from superagentx.llm.gemini import GeminiClient

logger = logging.getLogger(__name__)

'''
 Run Pytest:  

   1. pytest --log-cli-level=INFO tests/llm/test_gemini_client.py::TestGeminiClient::test_gemini_chat_completion
   2. pytest --log-cli-level=INFO tests/llm/test_openai_client.py::TestOpenAIClient::test_gemini_achat_completion
'''

# Define the function declaration for the model
weather_function = [{
    "name": "get_current_temperature",
    "description": "Gets the current temperature for a given location.",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "The city name, e.g. San Francisco",
            },
        },
        "required": ["location"],
    },
}]

# Start a conversation with the user message.
user_message = "What's the temperature in London?"

content = [
    {
        "role": "user",
        "content": user_message
    }
]


@pytest.fixture
def gemini_client_init() -> dict:
    llm_config = {'llm_type': 'gemini', 'model': 'gemini-2.0-flash'}
    llm_client: LLMClient = LLMClient(llm_config=llm_config)
    response = {'llm': llm_client}
    return response


class TestGeminiClient:

    async def test_gemini_client(self, gemini_client_init: dict):
        llm_client: LLMClient = gemini_client_init.get('llm').client
        assert isinstance(llm_client, GeminiClient)

    async def test_gemini_chat_completion(self, gemini_client_init: dict):
        llm_client: LLMClient = gemini_client_init.get('llm')

        chat_completion_params = ChatCompletionParams(
            messages=content,
            tools=weather_function
        )

        response = llm_client.chat_completion(chat_completion_params=chat_completion_params)
        logger.info(response)

    async def test_gemini_achat_completion(self, gemini_client_init: dict):
        llm_client: LLMClient = gemini_client_init.get('llm')

        chat_completion_params = ChatCompletionParams(
            messages=content,
            tools=weather_function
        )

        response = await llm_client.achat_completion(chat_completion_params=chat_completion_params)
        logger.info(response)
