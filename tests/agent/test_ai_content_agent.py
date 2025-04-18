import warnings

from superagentx.agentxpipe import AgentXPipe

with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=UserWarning)

import logging
import pytest
from superagentx.agent import Agent
from superagentx.browser_engine import BrowserEngine
from superagentx.engine import Engine
from superagentx.handler import AIHandler
from superagentx.llm import LLMClient
from superagentx.prompt import PromptTemplate

logger = logging.getLogger(__name__)

'''
 Run Pytest:  

   1. pytest --log-cli-level=INFO tests/agent/test_ai_content_agent.py::TestContentCreatorAgent::test_generation_agent
'''


@pytest.fixture
def agent_client_init() -> dict:
    llm_config = {'model': 'gpt-4o-mini', 'llm_type': 'openai'}
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
        content_creator_handler = AIHandler(llm=llm_client)

        prompt_template = PromptTemplate()

        content_creator_handler_engine = Engine(
            handler=content_creator_handler,
            llm=llm_client,
            prompt_template=prompt_template
        )

        browser_engine = BrowserEngine(
            llm=llm_client,
            prompt_template=prompt_template,
            # browser_instance_path="/usr/bin/google-chrome-stable"
        )

        goal = """Complete the user's input."""

        content_creator_agent = Agent(
            goal="Generate the content. Don't provide steps to automate the browser.",
            role="You are the Content Creator",
            llm=llm_client,
            prompt_template=prompt_template,
            max_retry=2,
            engines=[content_creator_handler_engine]
        )

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
                Wait for the content input from previous Agent and your job should be just to open x.com, login and post the content.
                DO NOT search content in the browser by your OWN. Properly understand the dom element and then create actions.

                Instructions:
                -------------

                Step 1: Formalize and summarise the input content
                Step 2: Open X.com, wait for user manual login
                Step 3: Go to the https://x.com/compose/post and write "Automated: Hello from SuperAgentX - Browser AI Agent" in the text box.
                Step 4: Review and post the tweet.

                Follow instructions carefully!
                """

        result = await pipe.flow(
            query_instruction=task
        )
        logger.info(f'Result ==> {result}')
        assert result
