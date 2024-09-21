
import pytest
from agentx.io.console import IOConsole

import logging
logger = logging.getLogger(__name__)

'''PyTest
   
    1. pytest -s --log-cli-level=INFO tests/io/test_console_io_stream.py::TestIOConsole::test_openai_client
'''


@pytest.fixture
def console_io() -> IOConsole:
    return IOConsole()


class TestIOConsole:

    async def test_openai_client(self, console_io: IOConsole):
        logging.info(f"IO Console Print & Input Test.")

        console_io.print("\033[32m", end="")
        console_io.print("Hello, Super AgentX World!", flush=True)

        # Getting input from the console
        data = console_io.input("Enter something: ")
        console_io.print(f"You entered: {data}", flush=True)
