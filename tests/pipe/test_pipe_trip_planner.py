import logging

import pytest

from superagentx.agent.agent import Agent
from superagentx.agent.engine import Engine
from superagentx.handler.ai import AIHandler
from superagentx.handler.serper_dev import SerperDevToolHandler
from superagentx.io import IOConsole
from superagentx.llm import LLMClient
from superagentx.agentxpipe import AgentXPipe
from superagentx.memory import Memory
from superagentx.prompt import PromptTemplate
from superagentx.utils.console_color import ConsoleColorType
from superagentx.utils.helper import iter_to_aiter
from superagentx.handler.scrape import ScrapeHandler

logger = logging.getLogger(__name__)

'''
 Run Pytest:  
   1.pytest -s --log-cli-level=INFO tests/pipe/test_pipe_trip_planner.py::TestTripPlannerPipe::test_planner_agent

'''


@pytest.fixture
def agent_client_init() -> dict:
    llm_config = {'model': 'gpt-4-turbo-2024-04-09', 'llm_type': 'openai'}
    serper_handler = SerperDevToolHandler()
    llm_client: LLMClient = LLMClient(llm_config=llm_config)
    response = {'llm': llm_client, 'llm_type': 'openai', 'serper_dev': serper_handler}
    return response


class TestTripPlannerPipe:

    @staticmethod
    async def _crawler_handler(
            query: str,
            serper_dev_handler: SerperDevToolHandler
    ) -> ScrapeHandler:
        datas = await serper_dev_handler.search(query=query, total_results=2)
        website_links = [data.get("link") async for data in iter_to_aiter(datas)]
        scrape_handler = ScrapeHandler(domain_url=website_links)
        return scrape_handler

    async def _construct_pipe(self, query: str, agent_client_init, crawler_handler):
        llm_client: LLMClient = agent_client_init.get('llm')
        prompt_template = PromptTemplate()
        memory = Memory()
        city_ai_handler = AIHandler(
            llm=llm_client,
            role="Analyze and select the best city for the trip based on specific criteria such as weather patterns, "
                 "seasonal events, and travel costs.",
            back_story="Detailed report on the chosen city including costs, weather forecast, and attractions"
        )
        local_expert_handler = AIHandler(
            llm=llm_client,
            role="As a local expert on this city you must compile an in-depth guide for someone traveling there and "
                 "wanting to have THE BEST trip ever!",
            back_story="Gather information about key attractions, local customs, "
                 "special events, and daily activity recommendations. Find the best spots to go to, the kind of place "
                 "only a local would know."
        )
        travel_concierge_handler = AIHandler(
            llm=llm_client,
            role="Amazing Travel Planner",
            back_story="Expand this guide into a full 7-day travel itinerary with detailed per-day plans, including "
                       "weather forecasts, places to eat, packing suggestions, and a budget breakdown. You MUST "
                       "suggest actual places to visit, actual hotels to stay and actual restaurants to go to."
        )
        crawl_engine = Engine(
            handler=crawler_handler,
            llm=llm_client,
            prompt_template=prompt_template
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
        crawl_agent = Agent(
            name="Crawler Agent",
            role='You are the data extract expert',
            goal='Extract the city, locations, weather, seasons, months and prices with full information',
            llm=llm_client,
            prompt_template=prompt_template,
            engines=[crawl_engine],
            memory=memory
        )
        city_selection_agent = Agent(
            name="City Selection Agent",
            role='City Selection Expert',
            goal='Select the best city based on weather, season, months, and prices',
            llm=llm_client,
            prompt_template=prompt_template,
            engines=[city_ai_engine],
            memory=memory
        )
        city_selection_agent.memory_id = crawl_agent.memory_id
        city_selection_agent.chat_id = crawl_agent.chat_id
        local_expert_agent = Agent(
            name="Local Expert Agent",
            role='Local Expert at the given city',
            goal='''
            you are a local expert city guide agent that highlights hidden gems, cultural hotspots, and practical travel.
            Include off-the-beaten-path attractions and experiences.
            Feature well-known cultural landmarks and venues (museums, theaters, etc.).
            Provide practical tips for travelers (transportation, local customs, best times to visit, etc.).
            ''',
            llm=llm_client,
            prompt_template=prompt_template,
            engines=[local_expert_engine]
        )
        travel_concierge_agent = Agent(
            name="Travel Concierge Agent",
            role='You are a Amazing Travel Plan Report Generator',
            goal='''Your final answer MUST be a complete expanded travel plan,
                formatted as markdown, encompassing a daily schedule,
                anticipated weather conditions, recommended clothing and
                items to pack, and a detailed budget, ensuring THE BEST
                TRIP EVER''',
            llm=llm_client,
            prompt_template=prompt_template,
            engines=[travel_concierge_engine],
            memory=memory
        )
        travel_concierge_agent.memory_id = crawl_agent.memory_id
        travel_concierge_agent.chat_id = crawl_agent.chat_id
        pipe = AgentXPipe(
            name="Trip Planner Pipe",
            agents=[crawl_agent, city_selection_agent, travel_concierge_agent]
        )
        return await pipe.flow(query)

    async def test_planner_agent(self, agent_client_init):
        serper_dev_handler: SerperDevToolHandler = agent_client_init.get("serper_dev")
        io_console = IOConsole()
        while True:
            await io_console.write(ConsoleColorType.CYELLOW2.value, end="")
            query_instruction = await io_console.read("User: ")
            crawl = await self._crawler_handler(query_instruction, serper_dev_handler)
            result = await self._construct_pipe(query_instruction, agent_client_init, crawl)
            await io_console.write(ConsoleColorType.CGREEN2.value, end="")
            await io_console.write(f"Assistant: {result}", flush=True)
