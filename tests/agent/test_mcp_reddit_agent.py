import json
import logging

import pytest

from superagentx.agent import Agent
from superagentx.engine import Engine
from superagentx.handler.mcp import MCPHandler
from superagentx.llm import LLMClient
from superagentx.prompt import PromptTemplate

logger = logging.getLogger(__name__)


@pytest.fixture
def agent_client_init() -> dict:
    llm_config = {'model': 'openai/gpt-5-mini'}
    llm_client: LLMClient = LLMClient(llm_config=llm_config)
    return {'llm': llm_client, 'llm_type': 'openai'}


async def status_callback(event: str, **kwargs):
    logger.info(f"[Callback] Event: {event}")
    logger.info(f"[Callback] Event: {event}, Data: {kwargs}")


class TestMCPRedditAgent:

    @pytest.mark.asyncio
    async def test_reddit_search_agent(self, agent_client_init: dict):
        llm_client: LLMClient = agent_client_init.get('llm')

        # MCP Tool - pip install mcp-server-reddit
        mcp_handler = MCPHandler(command="uvx", mcp_args=["mcp-server-reddit"])
        prompt_template = PromptTemplate()

        # ✅ Enable engine to execute MCP Tools
        mcp_engine = Engine(handler=mcp_handler, llm=llm_client, prompt_template=prompt_template)

        goal = "Review and perform user's input"

        # ✅ SuperAgentX Agent
        reddit_search_agent = Agent(
            goal=goal,
            role="You're an Analyst",
            llm=llm_client,
            prompt_template=prompt_template,
            max_retry=1
        )
        await reddit_search_agent.add(mcp_engine)

        # ✅ Ask question with live callback
        result = await reddit_search_agent.execute(
            query_instruction="What are the current hot posts on Reddit's frontpage and summarize?",
            status_callback=status_callback  # <-- callback passed here
        )

        # logger.info(f'Result ==> {result}')
        assert result
