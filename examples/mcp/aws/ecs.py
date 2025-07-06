import asyncio

from superagentx.agent import Agent
from superagentx.engine import Engine
from superagentx.handler.mcp import MCPHandler
from superagentx.llm import LLMClient
from superagentx.prompt import PromptTemplate


async def main():
    print("AWS ECS Analyser using SuperAgentX MCP Handler")

    # Step 1: Initialize LLM
    # Note: You need to setup your OpenAI API key before running this step.
    # export OPENAI_API_KEY=<your-api-key>
    llm_config = {"model": "gpt-4.1-mini", "llm_type": "openai"}
    llm_client = LLMClient(llm_config=llm_config)

    # Step 2: Setup MCP tool handler (AWS ECS)
    # Note: You need to install the awslabs.ecs-mcp-server package before running this step.
    # pip install awslabs.ecs-mcp-server
    # AWS credentials will be loaded from ~/.aws/credentials - Access Key, Secret Key, AWS_PROFILE, AWS_REGION
    mcp_handler = MCPHandler(command="uvx",
                             mcp_args=["--from", "awslabs-ecs-mcp-server", "ecs-mcp-server"],
                             env={
                                 "AWS_PROFILE" : "my_profile",
                                 "AWS_REGION": "us-east-1",
                                 "ALLOW_WRITE": "false",
                                 "ALLOW_SENSITIVE_DATA": "false"})

    # Step 3: Create Prompt Template
    prompt_template = PromptTemplate()

    # Step 4: Create Engine for ECS analysis using MCP
    ecs_engine = Engine(handler=mcp_handler, llm=llm_client,
                           prompt_template=prompt_template)

    # Step 5: Define AWS ECS Agent
    agent = Agent(goal="Summarize AWS ECS Details",
                  role="You're AWS ECS and Kubernetes Expert",
                  llm=llm_client, prompt_template=prompt_template, max_retry=1,
                  engines=[ecs_engine])

    result = await agent.execute(query_instruction="List all ECS clusters")

    print(f"ECS Agent Result : {result}")


if __name__ == "__main__":
    asyncio.run(main())