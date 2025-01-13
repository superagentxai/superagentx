
import asyncio

from rich import print as rprint
from superagentx.pipeimpl.awsvoicepipe import AWSVoicePipe

from create_pipe import get_superagentx_voice_to_text_pipe


async def main():
    """
    Launches the superagentx-voice-to-text pipeline console client for processing requests and handling data.
    """

    pipe = await get_superagentx_voice_to_text_pipe()

    # Create IO Cli Console - Interface
    io_pipe = AWSVoicePipe(
        search_name='SuperAgentX - Voice To Text',
        agentx_pipe=pipe,
        read_prompt=f"\n[bold green]Enter your search here"
    )
    await io_pipe.start()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, asyncio.CancelledError):
        rprint("\nUser canceled the [bold yellow][i]pipe[/i]!")
