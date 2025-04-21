import warnings


with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=UserWarning)

import logging
import pytest
from superagentx.agent import Agent
from superagentx.browser_engine import BrowserEngine
from superagentx.engine import Engine
from superagentx.handler import AIHandler
from superagentx.llm import LLMClient
from superagentx.llm.models import ChatCompletionParams
from superagentx.llm.gemini import GeminiClient
from superagentx.prompt import PromptTemplate

logger = logging.getLogger(__name__)

'''
 Run Pytest:  

   1. pytest --log-cli-level=INFO tests/agent/test_content_generation_agent.py::TestContentCreatorAgent::test_content_generator
'''


@pytest.fixture
def agent_client_init() -> dict:
    llm_config = {'llm_type': 'gemini', 'model': 'gemini-2.0-flash'}
    llm_client: LLMClient = LLMClient(llm_config=llm_config)
    response = {'llm': llm_client}
    return response


class TestContentCreatorAgent:

    async def test_content_generator(self, agent_client_init: dict):
        llm_client: LLMClient = agent_client_init.get('llm')
        content_creator_handler = AIHandler(
            llm=llm_client
        )

        prompt_template = PromptTemplate()

        content_creator_engine = Engine(
            handler=content_creator_handler,
            llm=llm_client,
            prompt_template=prompt_template
        )

        goal = """Create the digital marketing content"""

        search_agent = Agent(
            goal=goal,
            role="You are the analyst",
            llm=llm_client,
            max_retry=1,
            prompt_template=prompt_template,
            engines=[content_creator_engine]
        )

        result = await search_agent.execute(query_instruction='Create the digital marketing content')
        logger.info(f'Result ==> {result}')
