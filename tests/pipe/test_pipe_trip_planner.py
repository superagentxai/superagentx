import pytest

from agentx.agent.agent import Agent
from agentx.agent.engine import Engine
from agentx.handler.ai_handler import AIHandler
from agentx.llm import LLMClient
from agentx.prompt import PromptTemplate


@pytest.fixture
def agent_client_init() -> dict:
    llm_config = {'model': 'gpt-4-turbo-2024-04-09', 'llm_type': 'openai'}

    llm_client: LLMClient = LLMClient(llm_config=llm_config)
    response = {'llm': llm_client, 'llm_type': 'openai'}
    return response


class TestTripPlannerPipe:

    async def test_trip_planner(self, agent_client_init):
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
            name="Ecom Agent",
            goal="Get me the best search results",
            role="You are the best product searcher",
            llm=llm_client,
            prompt_template=prompt_template,
            engines=[ai_engine]
        )