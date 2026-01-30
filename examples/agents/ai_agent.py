import asyncio

from superagentx.agent import Agent
from superagentx.agentxpipe import AgentXPipe
from superagentx.engine import Engine
from superagentx.handler.ai import AIHandler
from superagentx.llm import LLMClient
from superagentx.prompt import PromptTemplate


async def main():
    print("Welcome to SuperAgentX AI Content Generator Tutorial")

    # Step 1: Initialize LLM
    # Note: You need to setup your OpenAI API key before running this step.
    # export OPENAI_API_KEY=<your-api-key>

    llm_config = {"model": "gpt-5-nano"}
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
    agent = Agent(goal="Generate content based on social media posts user input",
                  role="You're Content Generator",
                  llm=llm_client, prompt_template=prompt_template,
                  human_approval=True, max_retry=1,
                  engines=[content_engine])

    # result = await agent.execute(query_instruction="Create the digital marketing content")

    pipe = AgentXPipe(
        agents=[agent],
        workflow_store=True
    )
    task = "Create the digital marketing content"

    result = await pipe.flow(
        query_instruction=task
    )

    print(f"Agent Result : {result}")


if __name__ == "__main__":
    asyncio.run(main())
