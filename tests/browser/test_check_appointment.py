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

   1. pytest --log-cli-level=INFO tests/browser/test_check_appointment.py::test_check_appointment
'''


@pytest.fixture
def agent_client_init() -> dict:
    llm_config = {'model': 'gpt-4o', 'llm_type': 'openai'}

    llm_client: LLMClient = LLMClient(llm_config=llm_config)
    response = {'llm': llm_client, 'llm_type': 'openai'}
    return response


@pytest.mark.filterwarnings("ignore::UserWarning")
async def test_check_appointment(agent_client_init: dict):
    llm_client: LLMClient = agent_client_init.get('llm')
    prompt_template = PromptTemplate()
    browser_engine = BrowserEngine(
        llm=llm_client,
        prompt_template=prompt_template,
        # browser_instance_path="/usr/bin/google-chrome-stable"
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
        # memory=memory
    )

    task = (
        'Go to the Greece MFA webpage via the link I provided you.https://appointment.mfa.gr/en/reservations/aero/ireland-grcon-dub/'
        'Check the visa appointment dates. If there is no available date in this month, check the next month.'
        'If there is no available date in both months, tell me there is no available date.'
    )

    await pipe.flow(
        query_instruction=task
    )