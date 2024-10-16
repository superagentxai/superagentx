import logging

import pytest

from agentx.handler.ai_handler import AIHandler
from agentx.llm import LLMClient

logger = logging.getLogger(__name__)

'''
 Run Pytest:  

   1.pytest --log-cli-level=INFO tests/handlers/test_content_creator_async.py::TestContentCreator::test_text_content_creator

'''


@pytest.fixture
def content_creator_init() -> AIHandler:
    llm_config = {'model': 'gpt-4-turbo-2024-04-09', 'llm_type': 'openai'}

    llm_client: LLMClient = LLMClient(llm_config=llm_config)
    content_creator_handler = AIHandler(
        llm=llm_client
    )
    logger.info(content_creator_handler)
    return content_creator_handler


class TestContentCreator:

    async def test_text_content_creator(self, content_creator_init: AIHandler):
        result = await content_creator_init.text_creation(instruction='Create the digital marketing content')
        logger.info(f'Result => {result.choices[0].message.content}')
        assert "digital marketing" in result.choices[0].message.content
