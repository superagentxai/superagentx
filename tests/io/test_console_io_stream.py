
import pytest
from agentx.io.console import IOConsole
from agentx.utils.console_color import ConsoleColorType
import logging
logger = logging.getLogger(__name__)

'''PyTest
    1. pytest -s --log-cli-level=INFO tests/io/test_console_io_stream.py::TestIOConsole::test_console_io_input_print
    2. pytest -s --log-cli-level=INFO tests/io/test_console_io_stream.py::TestIOConsole::test_console_io_input_password
'''


@pytest.fixture
def console_io() -> IOConsole:
    return IOConsole()


class TestIOConsole:

    async def test_console_io_input_print(self, console_io: IOConsole):
        logging.info(f"IO Console Print & Input Test.")

        await console_io.write(ConsoleColorType.CYELLOW2.value, end="")
        await console_io.write("Hello, Super AgentX World!", flush=True)

        # Getting input from the console
        data = await console_io.read("Enter something: ")
        await console_io.write(f"You entered: {data}", flush=True)

    async def test_console_io_input_password(self, console_io: IOConsole):
        logging.info(f"IO Console Print & Input Password Test.")

        await console_io.write(ConsoleColorType.CGREEN.value, end="")
        await console_io.write("Hello, Super AgentX World!", flush=True)

        # Getting password input from the console
        data = await console_io.read("Enter something: ", password=True)
        await console_io.write(f"You entered: {data}", flush=True)
