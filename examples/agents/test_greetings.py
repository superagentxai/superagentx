
import logging

from superagentx.agent import Agent
from superagentx.agentxpipe import AgentXPipe
from superagentx.task_engine import TaskEngine

from superagentx.handler.task.general.dummy_handler import DummyHandler
from superagentx.handler.task.general.api_handler import APIHandler

logger = logging.getLogger(__name__)


'''
 Run Pytest:  

   1. pytest -s --log-cli-level=INFO tests/task/test_greetings.py::TestCrossHandlerPrevResult::test_cross_handler_prev_result
'''

class TestCrossHandlerPrevResult:

    async def test_cross_handler_prev_result(self):

        dummy_handler = DummyHandler()
        api_handler = APIHandler()

        # Engine 1
        dummy_engine = TaskEngine(
            handler=dummy_handler,
            instructions=[
                {"get_name": {}}
            ]
        )

        # Engine 2
        api_engine = TaskEngine(
            handler=api_handler,
            instructions=[
                {
                    "fetch_weather": {
                        "city": "$prev_result"
                    }
                }
            ]
        )

        dummy_agent = Agent(
            engines=[
                dummy_engine,
            ]
        )

        api_agent = Agent(
            engines=[
                api_engine
            ]
        )

        pipe = AgentXPipe(
            agents=[dummy_agent, api_agent],
            workflow_store=True
        )

        result = await pipe.flow(
            query_instruction="test"
        )

        print(f" Result {result}")