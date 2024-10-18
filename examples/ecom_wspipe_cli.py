import asyncio

from rich import print as rprint
from rich.prompt import Prompt

from websockets.asyncio.client import connect

from superagentx.utils.helper import sync_to_async


async def ecom_pipe_cli():
    """
    Launches the e-commerce pipeline websocket client for processing requests and handling data.
    """

    uri = "ws://localhost:8765"
    rprint(f'[bold blue]{10*'-'}Superagentx Ecom Websocket Cli{10*'-'}')

    async with connect(uri) as websocket:
        while True:
            query = await sync_to_async(Prompt.ask, '\n[bold green]Enter your search here')
            await websocket.send(query)
            res = await websocket.recv()
            rprint(f'{res}')


if __name__ == "__main__":
    asyncio.run(ecom_pipe_cli())
