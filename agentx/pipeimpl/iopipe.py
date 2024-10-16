from agentx.io import IOConsole
from agentx.pipe import AgentXPipe


class IOPipe:

    def __init__(
            self,
            agetnx_pipe: AgentXPipe,
            read_prompt: str | None = None,
            write_prompt: str | None = None
    ):
        self.agetnx_pipe = agetnx_pipe
        self.io_console = IOConsole(
            read_phrase=read_prompt,
            write_phrase=write_prompt
        )

    async def start(self):
        while True:
            query = await self.io_console.read()
            with await self.io_console.status("[bold yellow] Searching...\n"):
                pipe_result = await self.agetnx_pipe.flow(query_instruction=query)
                if pipe_result:
                    goal_result = pipe_result[-1]
                    await self.io_console.write(f'\n[bold cyan]Result:[/bold cyan] {goal_result.result}\n')
                    await self.io_console.write(f'\n[bold cyan]Reason[/bold cyan]:')
                    await self.io_console.json(data=goal_result.result)
                    await self.io_console.write(f'\n\n[bold cyan]Goal Satisfied[/bold cyan]: {goal_result.is_goal_satisfied}\n')
                else:
                    await self.io_console.write("\nNo results found!\n")
            await self.io_console.rule('[bold green]End')
