import asyncio
import json
import signal
from collections.abc import Callable, Awaitable
from json import JSONDecodeError

from rich.console import Console
from websockets.asyncio.server import ServerConnection, serve

from superagentx.pipe import AgentXPipe


class WSPipe:

    def __init__(
            self,
            *,
            search_name: str,
            agentx_pipe: AgentXPipe,
            ws_handler: Callable[[ServerConnection], Awaitable[None]] | None = None,
            host: str | None = None,
            port: int | None = None,
            **kwargs
    ):
        self.search_name = search_name
        self.agentx_pipe = agentx_pipe
        self._ws_handler = ws_handler or self.default_handler
        self.host = host or 'localhost'
        self.port = port or 8765
        self.kwargs = kwargs
        self._console = Console()
        self._result_not_found = "No results found!"

    async def default_handler(self, ws_conn: ServerConnection) -> None:
        async for query in ws_conn:
            r_as_json = False
            try:
                q_data = json.loads(query)
                q = q_data.get('query')
                r_as_json = True
            except JSONDecodeError:
                q = query
            self._console.print(f"Pipe Query: {q}")
            pipe_result = await self.agentx_pipe.flow(
                query_instruction=q
            )
            if pipe_result:
                goal_result = pipe_result[-1]
                if r_as_json:
                    result = goal_result.model_dump_json(exclude={'name', 'agent_id'})
                else:
                    result = (
                        f'\nResult:\n{json.dumps(goal_result.result)}\n'
                        f'\nReason: {goal_result.reason}\n'
                        f'\nGoal Satisfied: {goal_result.is_goal_satisfied}\n'
                    )
            else:
                result = json.dumps({'error': self._result_not_found}) if r_as_json else self._result_not_found
            self._console.print(f"Pipe Result:\n{result}")
            await ws_conn.send(result)

    async def start(self):
        self._console.rule(f'[bold blue]{self.search_name}')
        loop = asyncio.get_running_loop()
        stop = loop.create_future()
        loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)
        self._console.print(
            f'[bold yellow]:rocket: Starting SuperagentX websocket server\n'
            f':smiley: Host: {self.host}\n'
            f':smiley: Port: {self.port}'
        )
        async with serve(
                handler=self._ws_handler,
                host=self.host,
                port=self.port,
                **self.kwargs
        ):
            await stop
