import logging

import pytest

from superagentx.agent.agent import Agent
from superagentx.agent.engine import Engine
from superagentx.handler.ai import AIHandler
from superagentx.io import IOConsole
from superagentx.llm import LLMClient
from superagentx.pipe import AgentXPipe
from superagentx.prompt import PromptTemplate
from superagentx.utils.console_color import ConsoleColorType

logger = logging.getLogger(__name__)

'''
 Run Pytest:  
   1.pytest -s --log-cli-level=INFO tests/pipe/test_pipe_trip_planner.py::TestTripPlannerPipe::test_planner_agent

'''


@pytest.fixture
def agent_client_init() -> dict:
    llm_config = {'model': 'gpt-4-turbo-2024-04-09', 'llm_type': 'openai'}

    llm_client: LLMClient = LLMClient(llm_config=llm_config)
    response = {'llm': llm_client, 'llm_type': 'openai'}
    return response


class TestTripPlannerPipe:

    async def test_planner_agent(self, agent_client_init):
        llm_client: LLMClient = agent_client_init.get('llm')
        prompt_template = PromptTemplate()
        city_ai_handler = AIHandler(
            llm=llm_client,
            role="City Selection Expert",
            back_story="An expert in analyzing travel data to pick ideal destinations"
        )
        local_expert_handler = AIHandler(
            llm=llm_client,
            role="Local Expert at this city",
            back_story="A knowledgeable local guide with extensive information about the city, it's attractions and "
                       "customs"
        )
        travel_concierge_handler = AIHandler(
            llm=llm_client,
            role="Amazing Travel Concierge",
            back_story="Specialist in travel planning and logistics with decades of experience"
        )
        city_ai_engine = Engine(
            handler=city_ai_handler,
            llm=llm_client,
            prompt_template=prompt_template
        )
        local_expert_engine = Engine(
            handler=local_expert_handler,
            llm=llm_client,
            prompt_template=prompt_template
        )
        travel_concierge_engine = Engine(
            handler=travel_concierge_handler,
            llm=llm_client,
            prompt_template=prompt_template
        )
        city_selection_agent = Agent(
            name="City Selection Agent",
            role='City Selection Expert',
            goal='Select the best city based on weather, season, and prices',
            llm=llm_client,
            prompt_template=prompt_template,
            engines=[city_ai_engine]
        )
        local_expert_agent = Agent(
            name="Local Expert Agent",
            role='Local Expert at this city',
            goal='Provide the BEST insights about the selected city',
            llm=llm_client,
            prompt_template=prompt_template,
            engines=[local_expert_engine]
        )
        travel_concierge_agent = Agent(
            name="Travel Concierge Agent",
            role='Amazing Travel Concierge',
            goal="""Create the most amazing travel itineraries with budget and 
                    packing suggestions for the city""",
            llm=llm_client,
            prompt_template=prompt_template,
            engines=[travel_concierge_engine]
        )
        pipe = AgentXPipe(
            name="Trip Planner Pipe",
            agents=[city_selection_agent, local_expert_agent, travel_concierge_agent]
        )
        io_console = IOConsole()
        while True:
            await io_console.write(ConsoleColorType.CYELLOW2.value, end="")
            query_instruction = await io_console.read("User: ")
            result = await pipe.flow(query_instruction)
            await io_console.write(ConsoleColorType.CGREEN2.value, end="")
            await io_console.write(f"Assistant: {result}", flush=True)
