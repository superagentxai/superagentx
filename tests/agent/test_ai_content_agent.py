import warnings

from superagentx.agentxpipe import AgentXPipe

with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=UserWarning)

import logging
import pytest
from superagentx.agent import Agent
from superagentx.browser_engine import BrowserEngine
from superagentx.llm import LLMClient
from superagentx.prompt import PromptTemplate

logger = logging.getLogger(__name__)

'''
 Run Pytest:  

   1. pytest --log-cli-level=INFO tests/agent/test_ai_content_agent.py::TestContentCreatorAgent::test_generation_agent
'''


@pytest.fixture
def agent_client_init() -> dict:
    llm_config = {'model': 'gpt-4o', 'llm_type': 'openai'}
    # llm_config = {
    #     "model": 'anthropic.claude-3-5-haiku-20241022-v1:0',
    #     "llm_type": 'bedrock'
    # }

    llm_client: LLMClient = LLMClient(llm_config=llm_config)
    response = {'llm': llm_client, 'llm_type': 'openai'}
    return response


class TestContentCreatorAgent:

    @pytest.mark.filterwarnings("ignore::UserWarning")
    async def test_generation_agent(self, agent_client_init: dict):
        llm_client: LLMClient = agent_client_init.get('llm')

        prompt_template = PromptTemplate()

        browser_engine = BrowserEngine(
            llm=llm_client,
            prompt_template=prompt_template,
        )

        goal = """Complete the user's input."""

        browser_agent = Agent(
            goal=goal,
            role="You are the AI Assistant",
            llm=llm_client,
            prompt_template=prompt_template,
            max_retry=1,
            engines=[browser_engine]
        )

        pipe = AgentXPipe(
            agents=[browser_agent],
        )

        task = """
                Get a latest news about Generative AI Research! 
                """

        result = await pipe.flow(
            query_instruction=task
        )
        logger.info(f'Result ==> {result}')
        assert result
