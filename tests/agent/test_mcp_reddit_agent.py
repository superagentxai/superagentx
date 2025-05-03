import logging

import pytest

from superagentx.agent import Agent
from superagentx.engine import Engine
from superagentx.handler.mcp import MCPHandler
from superagentx.llm import LLMClient
from superagentx.prompt import PromptTemplate

logger = logging.getLogger(__name__)

'''
 Run Pytest:  

   1. pytest --log-cli-level=INFO tests/agent/test_mcp_reddit_agent.py::TestMCPRedditAgent::test_reddit_search_agent
'''


@pytest.fixture
def agent_client_init() -> dict:
    llm_config = {'model': 'gpt-4.1', 'llm_type': 'openai'}
    # llm_config = {'model': 'anthropic.claude-3-5-sonnet-20240620-v1:0', 'llm_type': 'anthropic'}

    llm_client: LLMClient = LLMClient(llm_config=llm_config)
    response = {'llm': llm_client, 'llm_type': 'openai'}
    return response


class TestMCPRedditAgent:

    @pytest.mark.asyncio
    async def test_reddit_search_agent(self, agent_client_init: dict):
        llm_client: LLMClient = agent_client_init.get('llm')

        # MCP Tool - pip install mcp-server-reddit
        mcp_handler = MCPHandler(command="uvx", mcp_args=["mcp-server-reddit"])

        prompt_template = PromptTemplate()

        # Enable Engine to execute MCP Tools
        mcp_engine = Engine(handler=mcp_handler, llm=llm_client,
                            prompt_template=prompt_template)

        goal = """ Review and perform user's input"""

        # SuperAgentX's Agent to run based on the goal
        reddit_search_agent = Agent(goal=goal, role="You're an Analyst",
                                    llm=llm_client, prompt_template=prompt_template)
        await reddit_search_agent.add(mcp_engine)

        # Ask Question and get results
        result = await reddit_search_agent.execute(query_instruction="What are the current hot posts on Reddit's "
                                                                     "frontpage?")
        logger.info(f'Result ==> {result}')
        assert result
