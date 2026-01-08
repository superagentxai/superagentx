import logging

import pytest
import json
from superagentx.agent import Agent

from superagentx.handler.task.general.api_handler import APIHandler
from superagentx.llm import LLMClient
from superagentx.task_engine import TaskEngine

logger = logging.getLogger(__name__)

'''
 Run Pytest:  

   1. pytest --log-cli-level=DEBUG tests/agent/task/weather.py::TestWeatherTaskAgent::test_weather_agent
'''


@pytest.fixture
def agent_client_init() -> dict:
    llm_config = {'model': 'gpt-4-turbo-2024-04-09', 'llm_type': 'openai'}

    llm_client: LLMClient = LLMClient(llm_config=llm_config)
    response = {'llm': llm_client, 'llm_type': 'openai'}
    return response


class TestWeatherTaskAgent:

    @pytest.mark.asyncio
    async def test_weather_agent(self, agent_client_init: dict):

        engine = TaskEngine(
            handler=APIHandler(),
            instructions=[

                # PARALLEL (weather OK, stock FAILS, news OK)
                [
                    {"fetch_weather": {"city": "San Francisco"}},
                    {"fetch_news": {"topic": "AI"}}
                ],

                # Combine using $prev.<method>
                {
                    "combine_successful": {
                        "weather": "$prev.fetch_weather",
                        "stock": "$prev.fetch_stock",  # will be None
                        "news": "$prev.fetch_news"
                    }
                }
            ]
        )

        weather_agent = Agent(engines=[engine], human_approval=True)

        result = await weather_agent.execute(query_instruction='')
        logger.info(f'Result ==> {result}')
        assert result
