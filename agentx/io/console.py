import getpass
from typing import Any

from agentx.io.base import IOStream


class IOConsole(IOStream):
    """A console input/output stream."""

    async def write(
            self,
            *objects: Any,
            sep: str | None = None,
            end: str | None = None,
            flush: bool = False
    ) -> None:
        """Print data to the output stream.

        Args:
            objects (any): The data to print.
            sep (str, optional): The separator between objects. Defaults to " ".
            end (str, optional): The end of the output. Defaults to "\n".
            flush (bool, optional): Whether to flush the output. Defaults to False.
        """
        sep = sep or " "
        end = end or "\n"
        print(
            *objects,
            sep=sep,
            end=end,
            flush=flush
        )

    async def read(
            self,
            prompt: str | None = None,
            *,
            password: bool = False
    ) -> str:
        """Read a line from the input stream.

        Args:
            prompt (str, optional): The prompt to display. Defaults to "".
            password (bool, optional): Whether to read a password. Defaults to False.

        Returns:
            str: The line read from the input stream.

        """
        prompt = prompt or ""

        if password:
            return getpass.getpass(prompt if prompt else "Password: ")
        return input(prompt)
