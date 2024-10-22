import asyncio
import json
import signal
from collections.abc import Callable, Awaitable
from json import JSONDecodeError

from rich.console import Console
from websockets.asyncio.server import ServerConnection, serve

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
            **kwargs
    ):
        """
        Initializes the WSPipe with necessary parameters for configuring an agentxpipe that interacts with a specified
        search mechanism and handles websocket connections.

        Args:
            search_name: The name of the search mechanism or service that the WSPipe will utilize. This name is used
                to identify the search functionality within the broader system.
            agentx_pipe: An instance of AgentXPipe that facilitates communication between the agent, engine and other
                components of the system. This pipe is crucial for data transfer and message handling within the
                agent's operational context.
            ws_handler: An optional callable that handles websocket connections. It takes a `ServerConnection`
                instance as an argument and returns an awaitable that processes incoming messages or events.
                If not provided, the WSPipe may use a default websocket handler.
            host: The hostname or IP address of the websocket server where the agentxpipe will be running.
                This parameter is important for establishing connections. Defaults to None, in which case the WSPipe
                may use a predefined host or local address.
            port: The port number on which the WSPipe will listen for incoming connections. This is crucial for network
                communication. Defaults to None, indicating that the WSPipe may use a standard port or a configured
                setting.
            kwargs: Additional keyword arguments that may be required for further customization or to pass additional
                configuration websocket server.

        """
        self.search_name = search_name
        self.agentx_pipe = agentx_pipe
        self._ws_handler = ws_handler or self.default_handler
        self.host = host or 'localhost'
        self.port = port or 8765
        self.kwargs = kwargs
        self._console = Console()
        self._result_not_found = "No results found!"

    async def default_handler(
            self,
            ws_conn: ServerConnection
    ) -> None:
        """
        Handles incoming websocket connections and processes messages.

        This asynchronous method is designed to manage websocket communication with clients.
        It receives a `ServerConnection` object representing the active websocket connection,
        allowing for real-time message handling and interaction.

        Args:
            ws_conn: An instance of `ServerConnection` that represents the active websocket connection to a client.
                This object provides methods and properties for sending and receiving messages, as well as managing
                the connection state.

        Returns:
            None
        """
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
