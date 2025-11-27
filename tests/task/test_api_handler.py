import logging
import json

from superagentx.task_engine import TaskEngine
from superagentx.handler.task.general.api_handler import APIHandler

logger = logging.getLogger(__name__)

'''
 Run Pytest:  

   1. pytest --log-cli-level=INFO tests/task/test_api_handler.py::TestAPIHandler::test_parallel_code
'''


class TestAPIHandler:

    async def test_parallel_code(self):
        engine = TaskEngine(
            handler=APIHandler(),
            instructions=[

                # PARALLEL (weather OK, stock FAILS, news OK)
                [
                    {"fetch_weather": {"city": "San Francisco"}},
                    {"fetch_stock": {"symbol": "AAPL"}},  # FAIL
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

        result = await engine.start()
        logger.info(f"Code : {json.dumps(result, indent=2)}")
