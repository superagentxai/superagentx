import aiohttp
import pytest
import logging

from superagentx.handler.base import BaseHandler
from superagentx.handler.decorators import tool
from superagentx.agent import Agent
from superagentx.agentxpipe import AgentXPipe
from superagentx.engine import Engine
from superagentx.llm import LLMClient
from superagentx.memory import Memory
from superagentx.prompt import PromptTemplate

logger = logging.getLogger(__name__)


class CoffeeCompassHandler(BaseHandler):

    @tool
    async def find_coffee_shops(self, latitude: str, longitude: str, radius: int = 1000) -> dict:
        """
            To find the best coffee shops based on given latitude and longitude.
        """

        overpass_url = "https://overpass-api.de/api/interpreter"
        query = f"""
                    [out:json];
                    (
                      node["amenity"="cafe"]
                        (around:{1000},{latitude},{longitude});
                    );
                    out body;
                    """
        async with aiohttp.ClientSession() as session:
            async with session.post(
                    url=overpass_url,
                    data=query
            ) as resp:
                result = await resp.json()
                return result

    @tool
    async def get_lat_long(
            self,
            place: str
    ) -> dict:
        """
        Get the coordinates of a city based on a location.

        Args:
            @param place: The place name

            @return result (Str): Return the real latitude & longitude for the given place.

        """

        header_dict = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                          " (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
            "referer": 'https://www.superagentx.ai'
        }
        url = "http://nominatim.openstreetmap.org/search"

        params = {
            'q': place,
            'format': 'json',
            'limit': 1
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    url=url,
                    params=params,
                    headers=header_dict
            ) as resp:
                resp_data = await resp.json()
                if resp_data:
                    lat = resp_data[0]["lat"]
                    lon = resp_data[0]["lon"]
                    return {
                        "latitude": lat,
                        "longitude": lon
                    }


async def get_coffeecompass_pipe(
        query_instruction: str,
        llm_client: LLMClient,
        memory: Memory
):
    coffee_compass_handler = CoffeeCompassHandler()

    # Set System Prompt to provide instructions for the LLM
    system_prompt = """
    You're provided with a tool that can get the coordinates for a specific city 'get_lat_long' and a tool that can
     get best cafe in that city, but requires the coordinates 'find_coffee_shops'; only use the tool if required. 
    You can call the tool multiple times in the same response. Don't make reference to the tools in your final answer.
    Generate ONLY the expected JSON
    """

    # Prompt Template
    coffee_shop_system_prompt = PromptTemplate(system_message=system_prompt)

    coffee_compass_engine = Engine(
        handler=coffee_compass_handler,
        llm=llm_client,
        prompt_template=coffee_shop_system_prompt
    )

    # Agent - Get latitude & longitude from Coffee Compass Handler using engine.
    lat_and_long_agent = Agent(
        name="Latitude Longitude Agent",
        role="You're a map expert to find latitude & longitude for the given place",
        goal="Get the latitude and longitude for the given place",
        llm=llm_client,
        max_retry=2,  # Default Max Retry is 5
        prompt_template=coffee_shop_system_prompt,
        engines=[coffee_compass_engine],
    )

    # Agent - To find Coffee shops nearby with an input of latitude & longitude.
    coffee_compass_agent = Agent(
        name='Cafe Finder Agent',
        goal="Find the good cafes with features list",
        role="You are the best cafe shop finder",
        llm=llm_client,
        max_retry=2,
        prompt_template=coffee_shop_system_prompt,
        engines=[coffee_compass_engine]
    )

    # Create Pipe - Interface

    # Pipe Interface to send it to publicly accessible interface (Cli Console / WebSocket / Restful API)
    pipe = AgentXPipe(
        agents=[lat_and_long_agent, coffee_compass_agent],
        memory=memory
    )
    return await pipe.flow(query_instruction=query_instruction)


_input = input(f"Enter your Query here: ")


@pytest.fixture
def user_input_init():
    return _input


'''
 Run Pytest:  

   1. pytest -s --log-cli-level=INFO tests/pipe/test_superagentx_all_llm.py::TestSuperAgentxAllLLM
'''


class TestSuperAgentxAllLLM:

    async def test_openai_client(self, user_input_init: str):
        logger.info(f"####################OpenAI Test Start#######################")
        llm_config = {"model": 'gpt-4o', "llm_type": 'openai'}

        llm_client: LLMClient = LLMClient(llm_config=llm_config)

        memory = Memory(memory_config={"llm_client": llm_client})

        pipe = await get_coffeecompass_pipe(
            query_instruction=user_input_init,
            llm_client=llm_client,
            memory=memory
        )
        try:
            assert isinstance(pipe, list)
            logger.info(f"####################OpenAI Test Complete#######################")
            await memory.delete()
        except Exception as ex:
            logger.info(f"####################OpenAI Test Failed#######################\n{ex}")

    async def test_bedrock_client(self, user_input_init: str):
        logger.info(f"####################Bedrock Test Start#######################")
        llm_config = {"model": 'anthropic.claude-3-5-haiku-20241022-v1:0', "llm_type": 'bedrock'}

        llm_client: LLMClient = LLMClient(llm_config=llm_config)

        memory = Memory(memory_config={"llm_client": llm_client})

        pipe = await get_coffeecompass_pipe(
            query_instruction=user_input_init,
            llm_client=llm_client,
            memory=memory
        )
        try:
            assert isinstance(pipe, list)
            logger.info(f"####################Bedrock Test Complete#######################")
            await memory.delete()
        except Exception as ex:
            logger.info(f"####################Bedrock Test Failed#######################\n{ex}")

    async def test_deepseek_client(self, user_input_init: str):
        logger.info(f"####################DeepSeek Test Start#######################")
        llm_config = {"llm_type": 'deepseek'}

        llm_client: LLMClient = LLMClient(llm_config=llm_config)

        memory = Memory(memory_config={"llm_client": llm_client})

        pipe = await get_coffeecompass_pipe(
            query_instruction=user_input_init,
            llm_client=llm_client,
            memory=memory
        )
        try:
            assert isinstance(pipe, list)
            logger.info(f"####################DeepSeek Test Complete#######################")
            await memory.delete()
        except Exception as ex:
            logger.info(f"####################DeepSeek Test Failed#######################\n{ex}")

    async def test_anthropic_client(self, user_input_init: str):
        logger.info(f"####################Anthropic Test Start#######################")
        llm_config = {"model": 'claude-3-7-sonnet-20250219', "llm_type": 'anthropic'}

        llm_client: LLMClient = LLMClient(llm_config=llm_config)

        memory = Memory(memory_config={"llm_client": llm_client})

        pipe = await get_coffeecompass_pipe(
            query_instruction=user_input_init,
            llm_client=llm_client,
            memory=memory
        )
        try:
            assert isinstance(pipe, list)
            logger.info(f"####################Anthropic Test Complete#######################")
            await memory.delete()
        except Exception as ex:
            logger.info(f"####################Anthropic Test Failed#######################\n{ex}")
