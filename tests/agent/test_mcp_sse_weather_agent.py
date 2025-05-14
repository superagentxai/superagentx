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

   1. pytest --log-cli-level=INFO tests/agent/test_mcp_sse_weather_agent.py::TestMCPWeatherAgent::test_weather_search_agent
'''


@pytest.fixture
def agent_client_init() -> dict:
    llm_config = {'model': 'gpt-4.1', 'llm_type': 'openai'}
    # llm_config = {'model': 'anthropic.claude-3-5-sonnet-20240620-v1:0', 'llm_type': 'anthropic'}

    llm_client: LLMClient = LLMClient(llm_config=llm_config)
    response = {'llm': llm_client, 'llm_type': 'openai'}
    return response


class TestMCPWeatherAgent:

    @pytest.mark.asyncio
    async def test_weather_search_agent(self, agent_client_init: dict):
        llm_client: LLMClient = agent_client_init.get('llm')

        # MCP Tool - SSE
        mcp_handler = MCPHandler(sse_url="http://0.0.0.0:8080/sse")

        weather_analyst = """You're a Weather Analyst. 
        1. For Forecast, get appropriate latitude & longitude. 
        2. For Weather alerts, convert city / state into TWO letter US code. Example CA, NY. Weather alerts, ONLY two letter 
        US code should be passed!.
        """
        prompt_template = PromptTemplate(system_message=weather_analyst)

        # Enable Engine to execute MCP Tools
        mcp_engine = Engine(handler=mcp_handler, llm=llm_client,
                            prompt_template=prompt_template)

        goal = """ Answer the weather alert or forcast report"""

        # SuperAgentX's Agent to run based on the goal
        weather_search_agent = Agent(goal=goal, role="You're a Weather Analyst", max_retry=1,
                                     llm=llm_client, prompt_template=prompt_template)
        await weather_search_agent.add(mcp_engine)

        # Ask Question and get results
        result = await weather_search_agent.execute(query_instruction="Get weather forecast for California!")
        logger.info(f'Result ==> {result}')
        assert result
