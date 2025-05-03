import logging

import pytest

from superagentx.agent import Agent
from superagentx.engine import Engine
from superagentx.llm import LLMClient
from superagentx.prompt import PromptTemplate

from superagentx.handler.mcp import MCPHandler

logger = logging.getLogger(__name__)

'''
 Run Pytest:  

   1. pytest --log-cli-level=INFO tests/agent/test_mcp_handler_agent.py::TestMCPAgent::test_math_calculations_agent
'''


@pytest.fixture
def agent_client_init() -> dict:
    llm_config = {'model': 'gpt-4-turbo-2024-04-09', 'llm_type': 'openai'}
    # llm_config = {'model': 'anthropic.claude-3-5-sonnet-20240620-v1:0', 'llm_type': 'anthropic'}
    llm_client: LLMClient = LLMClient(llm_config=llm_config)
    response = {'llm': llm_client, 'llm_type': 'openai'}
    return response


class TestMCPAgent:

    @pytest.mark.asyncio
    async def test_math_calculations_agent(self, agent_client_init: dict):
        llm_client: LLMClient = agent_client_init.get('llm')
        mcp_handler = MCPHandler(command="python",
                                 mcp_args=["-m", "mcp_server_time", "--local-timezone=America/New_York"])

        prompt_template = PromptTemplate()
        mcp_engine = Engine(
            handler=mcp_handler,
            llm=llm_client,
            prompt_template=prompt_template
        )

        goal = """ Get exact time and zone based on given timezone"""
        search_agent = Agent(
            goal=goal,
            role="Time zone",
            llm=llm_client,
            prompt_template=prompt_template
        )

        await search_agent.add(
            mcp_engine
        )

        result = await search_agent.execute(query_instruction="What time is it in Los Angeles?")
        logger.info(f'Result ==> {result}')
        assert result
