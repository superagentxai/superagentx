import asyncio
import os
import sys

from rich import print as rprint

from superagentx.memory import Memory

sys.path.extend([os.path.dirname(os.path.dirname(os.path.abspath(__file__)))])

from superagentx.agent.agent import Agent
from superagentx.agent.engine import Engine
from superagentx.handler.ecommerce.amazon import AmazonHandler
from superagentx.handler.ecommerce.walmart import WalmartHandler
from superagentx.llm import LLMClient
from superagentx.agentxpipe import AgentXPipe
from superagentx.pipeimpl.iopipe import IOPipe
from superagentx.prompt import PromptTemplate


async def main():
    """
    Launches the e-commerce pipeline console client for processing requests and handling data.
    """
    llm_config = {'llm_type': 'azure-openai'}

    llm_client: LLMClient = LLMClient(llm_config=llm_config)
    memory = Memory()
    amazon_ecom_handler = AmazonHandler(
        api_key="",
        country="IN"
    )
    walmart_ecom_handler = WalmartHandler(
        api_key="",
    )
    prompt_template = PromptTemplate()
    amazon_engine = Engine(
        handler=amazon_ecom_handler,
        llm=llm_client,
        prompt_template=prompt_template
    )
    walmart_engine = Engine(
        handler=walmart_ecom_handler,
        llm=llm_client,
        prompt_template=prompt_template
    )
    ecom_agent = Agent(
        name='Ecom Agent',
        goal="Get me the best search results",
        role="You are the best product searcher",
        llm=llm_client,
        prompt_template=prompt_template,
        engines=[[amazon_engine, walmart_engine]]
    )
    pipe = AgentXPipe(
        agents=[ecom_agent],
        memory=memory
    )
    io_pipe = IOPipe(
        search_name='SuperAgentX Ecom',
        agentx_pipe=pipe,
        read_prompt=f"\n[bold green]Enter your search here"
    )
    await io_pipe.start()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, asyncio.CancelledError):
        rprint("\nUser canceled the [bold yellow][i]pipe[/i]!")
