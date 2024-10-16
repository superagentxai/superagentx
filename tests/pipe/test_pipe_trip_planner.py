import logging

import pytest

from agentx.agent.agent import Agent
from agentx.agent.engine import Engine
from agentx.handler.ai_handler import AIHandler
from agentx.io import IOConsole
from agentx.llm import LLMClient
from agentx.pipe import AgentXPipe
from agentx.prompt import PromptTemplate
from agentx.utils.console_color import ConsoleColorType

logger = logging.getLogger(__name__)

'''
 Run Pytest:  
   1.pytest -s --log-cli-level=INFO tests/pipe/test_ai_pipe.py::TestIOConsolePipe::test_ai_spamfilter
   2.pytest -s --log-cli-level=INFO tests/pipe/test_ai_pipe.py::TestIOConsolePipe::test_writer
   3.pytest -s --log-cli-level=INFO tests/pipe/test_ai_pipe.py::TestIOConsolePipe::test_scorer
'''


@pytest.fixture
def agent_client_init() -> dict:
    llm_config = {'model': 'gpt-4-turbo-2024-04-09', 'llm_type': 'openai'}

    llm_client: LLMClient = LLMClient(llm_config=llm_config)
    response = {'llm': llm_client, 'llm_type': 'openai'}
    return response


class TestTripPlannerPipe:

    async def test_city_selection_agent(self, agent_client_init):
        llm_client: LLMClient = agent_client_init.get('llm')
        ai_handler = AIHandler(
            llm=llm_client,
            role="City Selection Expert",
            back_story="An expert in analyzing travel data to pick ideal destinations"
        )
        prompt_template = PromptTemplate()
        ai_engine = Engine(
            handler=ai_handler,
            llm=llm_client,
            prompt_template=prompt_template
        )
        city_selection_agent = Agent(
            name="City Selection Agent",
            role='City Selection Expert',
            goal='Select the best city based on weather, season, and prices',
            llm=llm_client,
            prompt_template=prompt_template,
            engines=[ai_engine]
        )
        pipe = AgentXPipe(
            agents=[city_selection_agent]
        )

        io_console = IOConsole()
        while True:
            await io_console.write(ConsoleColorType.CYELLOW2.value, end="")
            query_instruction = await io_console.read("User: ")
            result = await pipe.flow(query_instruction)
            await io_console.write(ConsoleColorType.CGREEN2.value, end="")
            await io_console.write(f"Assistant: {result}", flush=True)
