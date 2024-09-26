import pytest
import logging

from agentx.handler.content_creator import ContentCreatorHandler
from langchain_openai import ChatOpenAI
logger = logging.getLogger(__name__)

'''
 Run Pytest:  

   1.pytest --log-cli-level=INFO tests/handlers/test_content_creator_async.py::TestContentCreator::test_text_content_creator

'''

@pytest.fixture
def content_creator_init() -> ContentCreatorHandler:
    content_creator_handler = ContentCreatorHandler(
        prompt="Create the digital marketing content",
        llm=ChatOpenAI(model="gpt-4o")
    )
    logger.info(content_creator_handler)
    return content_creator_handler

class TestContentCreator:

    async def test_text_content_creator(self, content_creator_init: ContentCreatorHandler):
        result = await content_creator_init.text_creation()
        assert "digital marketing" in result

