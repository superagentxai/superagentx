import logging
import pytest
from agentx.agent.agent import Agent
from agentx.agent.engine import Engine
from agentx.handler.serper_dev import SerperDevToolHandler
from agentx.llm import LLMClient
from agentx.prompt import PromptTemplate

logger = logging.getLogger(__name__)

'''
 Run Pytest:  

   1. pytest --log-cli-level=INFO tests/agent/test_serper_agent.py::TestSerperDevAgent::test_search_agent
'''


@pytest.fixture
def agent_client_init() -> dict:
    llm_config = {'model': 'gpt-4-turbo-2024-04-09', 'llm_type': 'openai'}

    llm_client: LLMClient = LLMClient(llm_config=llm_config)
    response = {'llm': llm_client, 'llm_type': 'openai'}
    return response


class TestSerperDevAgent:

    async def test_search_agent(self, agent_client_init: dict):
        llm_client: LLMClient = agent_client_init.get('llm')
        serper_dev_handler = SerperDevToolHandler()

        prompt_template = PromptTemplate()
        serper_search_engine = Engine(
            handler=serper_dev_handler,
            llm=llm_client,
            prompt_template=prompt_template
        )

        goal = """
                List five AI companies started 2024."""
        search_agent = Agent(
            goal=goal,
            role="You are the analyst",
            llm=llm_client,
            prompt_template=prompt_template
        )

        await search_agent.add(
            serper_search_engine
        )

        result = await search_agent.execute()
        logger.info(f'Result ==> {result}')
        assert result
