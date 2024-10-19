import os

import pytest

from superagentx.agent.agent import Agent
from superagentx.agent.engine import Engine
from superagentx.handler.ai import AIHandler
from superagentx.handler.ecommerce.amazon import AmazonHandler
from superagentx.handler.ecommerce.flipkart import FlipkartHandler
from superagentx.io import IOConsole
from superagentx.llm import LLMClient
from superagentx.memory import Memory
from superagentx.agentxpipe import AgentXPipe
from superagentx.prompt import PromptTemplate

'''
 Run Pytest:  

   1. pytest -s --log-cli-level=INFO tests/pipe/test_pipe_ecom.py::TestEcommercePipe::test_ecom_pipe
'''


@pytest.fixture
def agent_client_init() -> dict:
    llm_config = {'model': 'gpt-4-turbo-2024-04-09', 'llm_type': 'openai'}

    llm_client: LLMClient = LLMClient(llm_config=llm_config)
    response = {'llm': llm_client, 'llm_type': 'openai'}
    return response


class TestEcommercePipe:

    async def test_ecom_pipe(self, agent_client_init: dict):
        llm_client: LLMClient = agent_client_init.get('llm')
        amazon_ecom_handler = AmazonHandler(
            api_key=os.getenv('RAPID_API_KEY'),
            country="IN"
        )
        flipkart_ecom_handler = FlipkartHandler(
            api_key=os.getenv('RAPID_API_KEY'),
        )
        ai_handler = AIHandler(
            llm=llm_client
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
        ai_engine = Engine(
            handler=ai_handler,
            llm=llm_client,
            prompt_template=prompt_template
        )
        memory = Memory()
        ecom_agent = Agent(
            name="Ecom Agent",
            goal="Get me the best search results",
            role="You are the best product searcher",
            llm=llm_client,
            prompt_template=prompt_template,
            engines=[[amazon_engine, flipkart_engine]],
            memory=memory
        )
        price_review_agent = Agent(
            name="Price Review Agent",
            goal="Get me the best one from the given context",
            role="You are the price reviewer",
            llm=llm_client,
            prompt_template=prompt_template,
            engines=[ai_engine],
            memory=memory
        )
        pipe = AgentXPipe(
            agents=[ecom_agent, price_review_agent]
        )
        io = IOConsole(
            read_phrase="\n\n\nEnter your query here:\n\n=>",
            write_phrase="\n\n\nYour result is =>\n\n"
        )
        while True:
            input_instruction = await io.read()
            result = await pipe.flow(query_instruction=input_instruction)
            await io.write(result)
