import logging

import pytest

from superagentx.handler.ai import AIHandler
from superagentx.llm import LLMClient

logger = logging.getLogger(__name__)

'''
 Run Pytest:

   1. pytest --log-cli-level=INFO tests/handlers/test_bedrock_ai_handler.py::TestBedrockAIHandler::test_ai_bedrock_message
'''



@pytest.fixture
def ai_bedrock_client_init() -> dict:
    llm_config = {'model': 'anthropic.claude-3-5-sonnet-20240620-v1:0', 'llm_type': 'bedrock', 'async_mode': True}

    llm_client: LLMClient = LLMClient(llm_config=llm_config)
    response = {'llm': llm_client}
    return response


class TestBedrockAIHandler:

    async def test_ai_bedrock_message(self, ai_bedrock_client_init: dict):
        llm_client: LLMClient = ai_bedrock_client_init.get('llm')

        content_handler = AIHandler(llm=llm_client)
        response = await content_handler.text_creation(system_message="You are an app that creates playlists for a "
                                                                      "radio station that plays rock and pop music. "
                                                                      "Only return song names and the artist.",
                                                       instruction="Make sure the songs are by artists from the "
                                                                   "United Kingdom.")
        logger.info(f"Response ==> {response}")
