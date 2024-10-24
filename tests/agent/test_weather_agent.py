import logging
import pytest
from superagentx.agent.agent import Agent
from superagentx.agent.engine import Engine
from superagentx.handler.serper_dev import SerperDevToolHandler
from superagentx.llm import LLMClient
from superagentx.prompt import PromptTemplate

logger = logging.getLogger(__name__)

'''
 Run Pytest:  

   1. pytest --log-cli-level=INFO tests/agent/test_serper_agent.py::TestSerperDevAgent::test_search_agent
'''


@pytest.fixture
def agent_client_init() -> dict:
    llm_config = {'model': 'anthropic.claude-3-5-sonnet-20241022-v2:0', 'llm_type': 'bedrock'}

    llm_client: LLMClient = LLMClient(llm_config=llm_config)
    response = {'llm': llm_client}
    return response


class TestWeatherAgent:

    async def test_weather(self, agent_client_init: dict):
        llm_client: LLMClient = agent_client_init.get('llm')

