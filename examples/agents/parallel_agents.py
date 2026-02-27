import asyncio

from superagentx.agent import Agent
from superagentx.agentxpipe import AgentXPipe
from superagentx.handler.ai import AIHandler
from superagentx.llm import LLMClient
from superagentx.prompt import PromptTemplate


async def main():
    print("Testing Parallel Agents in SuperAgentX")

    llm_config = {"model": "gemini/gemini-2.5-flash"}
    llm_client = LLMClient(llm_config=llm_config)

    handler = AIHandler(llm=llm_client)

    # Agent 1 – SEO Content
    agent_seo = Agent(
        goal="Generate SEO optimized content",
        role="SEO Content Writer",
        tool=handler,
        llm=llm_client,
        prompt_template=PromptTemplate(),
        max_retry=1
    )

    # Agent 2 – LinkedIn Post
    agent_linkedin = Agent(
        goal="Generate LinkedIn post",
        role="Social Media Strategist",
        tool=handler,
        llm=llm_client,
        prompt_template=PromptTemplate(),
        max_retry=1
    )

    # Agent 3 – Twitter Thread
    agent_twitter = Agent(
        goal="Generate Twitter thread",
        role="Twitter Growth Hacker",
        tool=handler,
        llm=llm_client,
        prompt_template=PromptTemplate(),
        max_retry=1
    )

    # All 3 agents run in PARALLEL
    pipe = AgentXPipe(
        agents=[[agent_seo, agent_linkedin, agent_twitter]],
        workflow_store=False
    )

    task = "Create marketing content about Agentic AI"

    result = await pipe.flow(query_instruction=task)

    print("Parallel Agent Result:")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
