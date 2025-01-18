import logging

import pytest

from superagentx.agent import Agent
from superagentx.engine import Engine
from superagentx.llm import LLMClient
from superagentx.agentxpipe import AgentXPipe
from superagentx.prompt import PromptTemplate

from superagentx.handler.openapi import OpenAPIHandler

logger = logging.getLogger(__name__)

'''
 Run Pytest:  

   1. pytest -s --log-cli-level=INFO tests/pipe/test_openapi_pipe.py::TestOpenAPIConsolePipe::test_openapi_agent

'''


@pytest.fixture
def openapi_client_init() -> dict:
    llm_config = {"model": 'anthropic.claude-3-5-haiku-20241022-v1:0', "llm_type": 'bedrock'}

    llm_client: LLMClient = LLMClient(llm_config=llm_config)

    openapi_handler = OpenAPIHandler(base_url='https://petstore.swagger.io/v2/', spec_url_path='swagger.json')

    # Set System Prompt to provide instructions for the LLM
    system_prompt = """ You're an OpenAPI client based on standard OpenAPI standard specification. Invoke petstore API
    to get status using the endpoint '/pet/findByStatus'. The query parameter for the API, in the below format

    "{'status': 'sold'}" 

    The status can be 'sold', 'pending', 'available'.

    Once you get response, analyse the response text and provide the summarization.
    You can call the tool multiple times in the same response. Don't make reference to the tools in your final answer.
    Generate ONLY the expected JSON
    """

    response = {'llm': llm_client, 'openapi_handler': openapi_handler, 'system_prompt': system_prompt}
    return response


class TestOpenAPIConsolePipe:

    async def test_openapi_agent(self, openapi_client_init: dict):
        llm_client: LLMClient = openapi_client_init.get('llm')
        system_prompt = openapi_client_init.get('system_prompt')
        openapi_handler = openapi_client_init.get('openapi_handler')

        # Prompt Template
        pet_store_system_prompt = PromptTemplate(system_message=system_prompt)

        openapi_engine = Engine(
            handler=openapi_handler,
            llm=llm_client,
            prompt_template=pet_store_system_prompt
        )

        # Agent - Get Pet store statues
        pet_store_status_agent = Agent(
            name="Pet Store",
            role="You're a pet store keeper to keep pet dog statuses ",
            goal="Get the pet status using pet store API",
            llm=llm_client,
            max_retry=2,  # Default Max Retry is 5
            prompt_template=pet_store_system_prompt,
            engines=[openapi_engine],
        )

        # Pipe Interface to send it to publicly accessible interface (Cli Console / WebSocket / Restful API)
        pipe = AgentXPipe(
            agents=[pet_store_status_agent]
        )

        result = await pipe.flow(query_instruction="List sold pet names and sold pet count ")
        logger.info(f"Pet status result => \n{result}")
        assert result
