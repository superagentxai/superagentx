import asyncio

from superagentx.agent import Agent
from superagentx.agentxpipe import AgentXPipe
from superagentx.engine import Engine
from superagentx.handler.ai import AIHandler
from superagentx.handler.task.greetings.welcome_handler import WelcomeHandler
from superagentx.llm import LLMClient
from superagentx.prompt import PromptTemplate
from superagentx.task_engine import TaskEngine


async def main():
    print("Welcome to SuperAgentX AI Content Generator Tutorial")

    llm_config = {"model": "gemini/gemini-2.5-flash"}
    llm_client = LLMClient(llm_config=llm_config)

    # Step 2: Setup MCP tool handler (Reddit trending analyzer)
    # Note: You need to install the mcp-server-reddit package before running this step.

    content_creator_handler = AIHandler(llm=llm_client)

    # Step 3: Create Prompt Template
    prompt_template = PromptTemplate()

    # Step 4: Create Engine for Reddit analysis using MCP
    content_engine = Engine(handler=content_creator_handler, llm=llm_client,
                            prompt_template=prompt_template)

    # Step 5: Define Reddit Agent
    agent = Agent(goal="Generate a Greetings Message",
                  role="You're Content Generator",
                  llm=llm_client, prompt_template=prompt_template,
                  tool=content_creator_handler,
                  human_approval=True, max_retry=1
                  )

    handler = WelcomeHandler(first_name="John", last_name="Doe")

    engine = TaskEngine(
        handler=handler,
        instructions=[
            {"get_first_name": {}},
            {"send_greeting": {"message": "Hello, $prev.first_name $prev.last_name !"}}
        ]
    )

    greetings_agent = Agent(engines=[engine])
    # result = await agent.execute(query_instruction="Create the digital marketing content")

    pipe = AgentXPipe(
        agents=[agent, greetings_agent],
        workflow_store=True
    )
    task = "Greet User"

    result = await pipe.flow(
        query_instruction=task
    )

    print(f"Agent Result : {result}")


if __name__ == "__main__":
    asyncio.run(main())
