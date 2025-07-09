import json
from collections.abc import Callable, Awaitable
from json import JSONDecodeError
from urllib.parse import urlparse, parse_qs

from rich.console import Console
from websockets.asyncio.server import ServerConnection, serve
from websockets.exceptions import ConnectionClosedOK
from superagentx.agentxpipe import AgentXPipe


class WSPipe:

    def __init__(
            self,
            *,
            search_name: str,
            agentx_pipe: AgentXPipe,
            ws_handler: Callable[[ServerConnection], Awaitable[None]] | None = None,
            host: str | None = None,
            port: int | None = None,
            valid_api_keys: list[str] | None = None,
            **kwargs
    ):
        self.search_name = search_name
        self.agentx_pipe = agentx_pipe
        self._ws_handler = ws_handler or self.default_handler
        self.host = host or 'localhost'
        self.port = port or 8765
        self._valid_api_keys = set(valid_api_keys) if valid_api_keys else set()
        self.kwargs = kwargs
        self._console = Console()
        self._result_not_found = "No results found!"

    async def default_handler(
            self,
            ws_conn: ServerConnection
    ) -> None:
        try:
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
                        result = goal_result.model_dump_json(
                            exclude={'name', 'agent_id'},
                            exclude_none=True
                        )
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
        except ConnectionClosedOK:
            self._console.print("Client disconnected gracefully.")
        except Exception as e:
            self._console.print(f"[bold red]Error in default_handler: {e}[/bold red]")

    async def _authenticate_connection(self, ws_conn: ServerConnection) -> bool:
        if not self._valid_api_keys:
            return True  # No authentication required

        parsed_url = urlparse(ws_conn.request.path)
        query_params = parse_qs(parsed_url.query)
        api_key_from_query = query_params.get('token', [None])[0]

        if api_key_from_query in self._valid_api_keys:
            self._console.print(f"[bold green]Client authenticated with API key: {api_key_from_query}[/bold green]")
            return True
        else:
            self._console.print("[bold red]Authentication failed: Invalid or missing API key.[/bold red]")
            await ws_conn.close(code=1008, reason="Authentication failed")
            return False

    async def authenticated_handler(self, ws_conn: ServerConnection) -> None:
        if await self._authenticate_connection(ws_conn):
            await self._ws_handler(ws_conn)
        else:
            self._console.print("Connection denied due to failed authentication.")

    async def start(self) -> None:
        """
        Starts the WebSocket server. If valid API keys are provided, enables authentication.
        """
        self._console.rule(f'[bold blue]{self.search_name}')
        self._console.print(
            f'[bold yellow]:rocket: Starting SuperagentX websocket server\n'
            f':smiley: Host: {self.host}\n'
            f':smiley: Port: {self.port}'
        )

        selected_handler = self.authenticated_handler if self._valid_api_keys else self._ws_handler

        async with serve(
                handler=selected_handler,
                host=self.host,
                port=self.port,
                **self.kwargs
        ) as server:
            await server.serve_forever()
