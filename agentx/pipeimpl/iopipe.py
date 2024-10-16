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
            query = await self.io_console.read(
                f'\n\n{'='*10} Search Start {'='*10}\n\n'
                f'Enter your search here :=> '
            )
            pipe_result = await self.agetnx_pipe.flow(query_instruction=query)
            if pipe_result:
                goal_result = pipe_result[-1]
                await self.io_console.write(
                    f'\nResult: {goal_result.result}\n\n',
                    f'Reason: {goal_result.reason}\n\n',
                    f'Goal Satisfied: {goal_result.is_goal_satisfied}\n\n{'='*10} Search End {'='*10}\n\n'
                )
            else:
                await self.io_console.write("\nNo results found!\n")
