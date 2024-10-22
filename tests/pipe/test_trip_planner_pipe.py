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
   1.pytest -s --log-cli-level=INFO tests/pipe/test_trip_planner_pipe.py::TestTripPlannerPipe::test_planner_agent

'''

output_prompt = """
Destination: [Insert City/Country Name]
Duration: [Insert Number of Days]

Cities:
    [Insert City Here] - [Insert Locations]

Accommodation Details:

    Hotel Name: [Insert Hotel Name]
    Location: [Insert Hotel Address]
    Check-in: [Insert Check-in Date]
    Check-out: [Insert Check-out Date]
    Price: [Insert Price]

Must-Visit Attractions:

    [Insert Attraction Name] – [Insert Brief description and importance]
    [Insert Attraction Name] – [Insert Brief description and importance]

Hidden Gems:

    [Insert Location/Activity Name] – [Insert Brief description and why it’s a hidden gem]
    [Insert Location/Activity Name] – [Insert Brief description]

Cultural Hotspots:

    [Insert Landmark/Event Name] – [Insert Description of cultural significance]
    [Insert Museum/Art Gallery/Theater Name] – [Insert Description of importance]

Practical Travel Tips:

    Local Customs: [Insert Description of local etiquette or customs]
    Best Time to Visit: [Insert Weather conditions and recommended season]
    Currency Exchange: [Insert Currency details and exchange advice]
    Transportation Tips: [Insert Details on public transport, taxis, etc.]
    Emergency Contacts: [Insert Local emergency numbers, embassy contact information]
"""


@pytest.fixture
def agent_client_init() -> dict:
    llm_config = {'model': 'gpt-4o-2024-08-06', 'llm_type': 'openai'}
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
        datas = await serper_dev_handler.search(query=query, total_results=5)
        logger.info(f"Website Datas: {datas}")
        website_links = [data.get("link") async for data in iter_to_aiter(datas)]
        logger.info(f"Website Links: {website_links}")
        scrape_handler = ScrapeHandler(domain_urls=website_links)
        return scrape_handler

    async def _construct_pipe(self, query: str, agent_client_init, crawler_handler):
        llm_client: LLMClient = agent_client_init.get('llm')
        prompt_template = PromptTemplate()
        city_ai_handler = AIHandler(
            llm=llm_client,
            role="City Selection Expert",
            back_story="An expert in analyzing travel data to pick ideal destinations"
        )
        travel_concierge_handler = AIHandler(
            llm=llm_client,
            role="Amazing Travel Concierge",
            back_story="Specialist in travel planning and logistics with decades of experience"
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
        travel_concierge_engine = Engine(
            handler=travel_concierge_handler,
            llm=llm_client,
            prompt_template=prompt_template
        )
        crawl_agent = Agent(
            name="Crawler Agent",
            role=f'You are the travel data extractor. Extract the city, locations, hotels, weather, seasons, months and prices with full information based on the user question and context. And generate the below output format \n\n{output_prompt}',
            goal='Extract the city, locations, hotels, weather, seasons, months and prices',
            llm=llm_client,
            prompt_template=prompt_template,
            engines=[crawl_engine],
            output_format=output_prompt
        )
        city_selection_agent = Agent(
            name="City Selection Agent",
            role='City Selection Expert',
            goal='Select the best city based on weather, locations, hotels season, months, itineraries and prices',
            llm=llm_client,
            prompt_template=prompt_template,
            engines=[city_ai_engine]
        )
        travel_concierge_agent = Agent(
            name="Trip Planner Agent",
            role='Amazing Trip planner',
            goal='Create the most amazing travel with budget and packing suggestions for the city',
            llm=llm_client,
            prompt_template=prompt_template,
            engines=[travel_concierge_engine]
        )
        return crawl_agent, city_selection_agent, travel_concierge_agent

    async def test_planner_agent(self, agent_client_init):
        serper_dev_handler: SerperDevToolHandler = agent_client_init.get("serper_dev")
        io_console = IOConsole()
        memory = Memory()
        pipe = AgentXPipe(
            name="Trip Planner Pipe",
            memory=memory
        )
        while True:
            await io_console.write(ConsoleColorType.CYELLOW2.value, end="")
            query_instruction = await io_console.read("User: ")
            crawl = await self._crawler_handler(query_instruction, serper_dev_handler)
            crawl_agent, city_selection_agent, travel_concierge_agent = await self._construct_pipe(
                query_instruction,
                agent_client_init,
                crawl
            )
            pipe.agents = [crawl_agent, city_selection_agent, travel_concierge_agent]
            res = await pipe.flow(query_instruction)
            await io_console.write(ConsoleColorType.CGREEN2.value, end="")
            await io_console.write(f"Assistant: {res}", flush=True)