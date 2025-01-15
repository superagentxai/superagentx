from superagentx.agent import Agent
from superagentx.engine import Engine
from superagentx.llm import LLMClient
from superagentx.agentxpipe import AgentXPipe
from superagentx.prompt import PromptTemplate

from superagentx.handler.openapi import OpenAPIHandler
import asyncio


class OpenAPISpecAgent:

    def __init__(self, llm_client: LLMClient, openapi_handler: OpenAPIHandler):
        self.llm_client: LLMClient = llm_client
        self.openapi_handler: OpenAPIHandler = openapi_handler

    async def openapi_agent(self, system_prompt: str, user_input: str):
        # Prompt Template
        pet_store_system_prompt = PromptTemplate(system_message=system_prompt)

        openapi_engine = Engine(
            handler=self.openapi_handler,
            llm=self.llm_client,
            prompt_template=pet_store_system_prompt
        )

        # Agent - Get Pet store statues
        pet_store_status_agent = Agent(
            name="Pet Store",
            role="You're a pet store keeper to keep pets stock statuses ",
            goal="Get the pet status using pet store API",
            llm=self.llm_client,
            max_retry=2,  # Default Max Retry is 5
            prompt_template=pet_store_system_prompt,
            engines=[openapi_engine],
        )

        # Pipe Interface to send it to publicly accessible interface (Cli Console / WebSocket / Restful API)
        pipe = AgentXPipe(
            agents=[pet_store_status_agent]
        )

        goal_result = await pipe.flow(query_instruction=user_input)
        return goal_result


if __name__ == "__main__":

    # Path to the OpenAPI specification file (JSON or YAML)
    SPEC_PATH = "swagger.json"  # Replace with your spec file path
    BASE_URL = "https://petstore.swagger.io/v2"

    llm_config = {"model": 'anthropic.claude-3-5-haiku-20241022-v1:0', "llm_type": 'bedrock'}

    # Set System Prompt to provide instructions for the LLM
    system_prompt = """ You're an OpenAPI client based on standard OpenAPI standard specification. Invoke petstore API
        to get status using the endpoint '/pet/findByStatus'. The query parameter for the API, in the below format

        "{'status': 'sold'}" 

        The status can be 'sold', 'pending', 'available'.

        Once you get response, analyse the response text and provide the summarization.
        You can call the tool multiple times in the same response. Don't make reference to the tools in your final answer.
        Generate ONLY the expected JSON
        """

    openapi_handler = OpenAPIHandler(base_url=BASE_URL, spec_url_path=SPEC_PATH)
    llm_client: LLMClient = LLMClient(llm_config=llm_config)

    # Initialize the parser
    parser = OpenAPISpecAgent(llm_client=llm_client, openapi_handler=openapi_handler)

    user_input = input("User: ")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(parser.openapi_agent(system_prompt=system_prompt, user_input=user_input))
    loop.close()
    print(result)
