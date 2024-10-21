from rich.console import Console
from rich.prompt import Prompt

from superagentx.agentxpipe import AgentXPipe


class IOPipe:

    def __init__(
            self,
            *,
            search_name: str,
            agentx_pipe: AgentXPipe,
            read_prompt: str | None = None,
            write_prompt: str | None = None
    ):
        """
        Initializes the IOPipe with necessary parameters for configuring an agentxpipe that interacts with a specified
        search mechanism and handles websocket connections.

        Args:
            search_name: The name of the search mechanism or service that the IOPipe will utilize. This name is used
                to identify the search functionality within the broader system.
            agentx_pipe: An instance of AgentXPipe that facilitates communication between the agent, engine and other
                components of the system. This pipe is crucial for data transfer and message handling within the
                agent's operational context.
            read_prompt: An optional prompt string used for guiding the reading information.
                This prompt can help shape the queries made during the search operation. Defaults to None
                if not provided.
            write_prompt: An optional prompt string used for guiding the writing of information.
                This prompt may assist in structuring the responses or data being sent. Defaults to None
                if not provided.
        """
        self.search_name = search_name
        self.agentx_pipe = agentx_pipe
        self._read_prompt = read_prompt or ''
        self._write_prompt = write_prompt or ''
        self._console = Console()

    async def start(self) -> None:
        """
        Initiates the main process or operation of the class.

        This asynchronous method is responsible for starting the primary functionality of
        the class instance. It may involve setting up necessary resources, establishing
        connections, and beginning the main event loop or workflow that the class is designed
        to perform.

        Returns:
            None
        """
        self._console.rule(f'[bold blue]{self.search_name}')
        while True:
            query = Prompt.ask(
                prompt=self._read_prompt,
                console=self._console
            )
            with self._console.status("[bold yellow]Searching...\n", spinner='bouncingBall') as status:
                pipe_result = await self.agentx_pipe.flow(query_instruction=query)
                if pipe_result:
                    goal_result = pipe_result[-1]
                    if self._write_prompt:
                        self._console.print(self._write_prompt)
                    self._console.print(f'\n[bold cyan]Result[/bold cyan]:')
                    self._console.print_json(data=goal_result.result)
                    self._console.print(f'\n[bold cyan]Reason:[/bold cyan]: {goal_result.reason}\n')
                    self._console.print(f'\n[bold cyan]Goal Satisfied[/bold cyan]: {goal_result.is_goal_satisfied}\n')
                else:
                    self._console.print("\nNo results found!\n")
            self._console.rule('[bold green]End')
