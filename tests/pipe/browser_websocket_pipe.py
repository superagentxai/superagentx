import asyncio
from rich import print as rprint
from superagentx.pipeimpl.wspipe import WSPipe
from tests.pipe.browser_pipe import get_browser_pipe


async def main():
    pipe = await get_browser_pipe()

    ws_pipe = WSPipe(
        search_name='SuperAgentX Browser Agent Websocket Server',
        agentx_pipe=pipe,
        host="0.0.0.0"
    )
    await ws_pipe.start()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, asyncio.CancelledError):
        rprint("\nUser canceled the [bold yellow][i]pipe[/i]!")
