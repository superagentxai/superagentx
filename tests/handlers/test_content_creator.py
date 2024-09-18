import pytest

from agentx.handler.content_creator import ContentCreatorHandler
from langchain_openai import ChatOpenAI

'''
 Run Pytest:  

   1.pytest --log-cli-level=INFO tests/handlers/test_content_creator.py::TestContentCreator::test_text_content_creator

'''

@pytest.fixture
def content_creator_init() -> ContentCreatorHandler:
    content_creator_handler = ContentCreatorHandler(
        prompt="Create the digital marketing content",
        llm=ChatOpenAI(model="gpt-4o")
    )
    return content_creator_handler

class TestContentCreator:

    def test_text_content_creator(self, content_creator_init: ContentCreatorHandler):
        result = content_creator_init.handle(action="TEXT")
        assert "digital marketing" in result

