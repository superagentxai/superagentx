import logging

from superagentx.task_engine import TaskEngine
from superagentx.handler.task.greetings.welcome_handler import WelcomeHandler

logger = logging.getLogger(__name__)

'''
 Run Pytest:  

   1. pytest --log-cli-level=INFO tests/task/test_greetings.py::TestGreetings::test_greetings
'''


class TestGreetings:

    async def test_greetings(self):
        handler = WelcomeHandler(first_name="John", last_name="Doe")

        engine = TaskEngine(
            handler=handler,
            instructions=[
                {"get_first_name": {}},
                {"send_greeting": {"message": "Hello, $prev.first_name $prev.last_name !"}}
            ]
        )

        result = await engine.start()
        logger.info(f"Code : {result}")
