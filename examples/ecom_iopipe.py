import asyncio
import os
import sys

from rich import print as rprint

sys.path.extend([os.path.dirname(os.path.dirname(os.path.abspath(__file__)))])

from agentx.agent.agent import Agent
from agentx.agent.engine import Engine
from agentx.handler.ecommerce.amazon import AmazonHandler
from agentx.handler.ecommerce.flipkart import FlipkartHandler
from agentx.llm import LLMClient
from agentx.pipe import AgentXPipe
from agentx.pipeimpl.iopipe import IOPipe
from agentx.prompt import PromptTemplate


async def main():
    llm_config = {'model': 'gpt-4-turbo-2024-04-09', 'llm_type': 'openai'}

    llm_client: LLMClient = LLMClient(llm_config=llm_config)
    amazon_ecom_handler = AmazonHandler(
        api_key=os.getenv('RAPID_API_KEY'),
        country="IN"
    )
    flipkart_ecom_handler = FlipkartHandler(
        api_key=os.getenv('RAPID_API_KEY'),
    )
    prompt_template = PromptTemplate()
    amazon_engine = Engine(
        handler=amazon_ecom_handler,
        llm=llm_client,
        prompt_template=prompt_template
    )
    flipkart_engine = Engine(
        handler=flipkart_ecom_handler,
        llm=llm_client,
        prompt_template=prompt_template
    )
    ecom_agent = Agent(
        name='Ecom Agent',
        goal="Get me the best search results",
        role="You are the best product searcher",
        llm=llm_client,
        prompt_template=prompt_template,
        engines=[[amazon_engine, flipkart_engine]]
    )
    pipe = AgentXPipe(
        agents=[ecom_agent]
    )
    io_pipe = IOPipe(
        agetnx_pipe=pipe,
        read_prompt=f"\n[bold green]Enter your search here",
    )
    await io_pipe.io_console.rule("[bold blue]SuperAgentX Ecom")
    await io_pipe.start()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, asyncio.CancelledError):
        rprint("\nUser canceled the [bold yellow][i]pipe[/i]!")
