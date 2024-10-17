from typing import Any

from rich import print as rprint
from rich.console import Console
from rich.prompt import Prompt

from superagentx.io.base import IOStream


class IOConsole(IOStream):
    """A console input/output stream."""

    def __init__(
            self,
            read_phrase: str | None = None,
            write_phrase: str | None = None
    ):
        self.read_phrase = read_phrase or ''
        self.write_phrase = write_phrase or ''
        self._console = Console()

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "<IOConsole>"

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
        rprint(
            self.write_phrase,
            *objects,
            sep=sep,
            end=end,
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
        prompt = prompt or self.read_phrase
        return Prompt.ask(
            prompt=prompt,
            console=self._console,
            password=password
        )

    async def rule(
            self,
            title: str
    ):
        self._console.rule(title)

    async def json(
            self,
            data: list | dict
    ):
        self._console.print_json(data=data)

    async def status(
            self,
            status_msg: str
    ):
        return self._console.status(
            status_msg,
            spinner='bouncingBall'
        )
