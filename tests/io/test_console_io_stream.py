
import pytest
from agentx.io.console import IOConsole
from agentx.utils.console_color import ConsoleColorType
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

        await console_io.print(ConsoleColorType.CYELLOW2.value, end="")
        await console_io.print("Hello, Super AgentX World!", flush=True)

        # Getting input from the console
        data = await console_io.input("Enter something: ")
        await console_io.print(f"You entered: {data}", flush=True)
