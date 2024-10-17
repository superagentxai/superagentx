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
        self.search_name = search_name
        self.agentx_pipe = agentx_pipe
        self._read_prompt = read_prompt or ''
        self._write_prompt = write_prompt or ''
        self._console = Console()

    async def start(self):
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
