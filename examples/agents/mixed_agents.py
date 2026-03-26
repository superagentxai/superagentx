import asyncio
import time

from superagentx.agent import Agent
from superagentx.agentxpipe import AgentXPipe
from superagentx.router.router_engine import RouterEngine
from superagentx.handler.ai import AIHandler
from superagentx.llm import LLMClient
from superagentx.prompt import PromptTemplate


async def main():
    print("🚀 SuperAgentX Mixed Sequential + Parallel Demo (With Router)")

    start_time = time.time()

    # ----------------------------
    # LLM Config
    # ----------------------------
    llm_config = {"model": "gemini/gemini-2.5-flash"}
    llm_client = LLMClient(llm_config=llm_config)

    handler = AIHandler(llm=llm_client)

    # ----------------------------
    # Research Agent (Sequential)
    # ----------------------------
    research_agent = Agent(
        name="Research Agent",
        goal="Research and outline key points about Agentic AI in digital marketing",
        role="research_agent",
        tool=handler,
        llm=llm_client,
        prompt_template=PromptTemplate(),
        max_retry=1
    )

    research_agent.capabilities = ["research", "analysis"]

    # ----------------------------
    # Blog Content Agent (Parallel)
    # ----------------------------
    blog_agent = Agent(
        name="Blog Agent",
        goal="Generate a detailed blog article based on the research",
        role="blog_agent",
        tool=handler,
        llm=llm_client,
        prompt_template=PromptTemplate(),
        max_retry=1
    )

    blog_agent.capabilities = ["blog", "article", "longform"]

    # ----------------------------
    # LinkedIn Post Agent (Parallel)
    # ----------------------------
    linkedin_agent = Agent(
        name="LinkedIn Agent",
        goal="Create an engaging LinkedIn post based on the research",
        role="linkedin_agent",
        tool=handler,
        llm=llm_client,
        prompt_template=PromptTemplate(),
        max_retry=1
    )

    linkedin_agent.capabilities = ["linkedin", "social", "post"]

    # ----------------------------
    # Final Editor Agent (Sequential)
    # ----------------------------
    editor_agent = Agent(
        name="Editor Agent",
        goal="Combine blog and LinkedIn content into a cohesive final output",
        role="editor_agent",
        tool=handler,
        llm=llm_client,
        prompt_template=PromptTemplate(),
        max_retry=1
    )

    editor_agent.capabilities = ["edit", "grammar"]

    # ----------------------------
    # Router Setup
    # ----------------------------
    router = RouterEngine(
        llm=llm_client,
        mode="capability"
    )

    # ----------------------------
    # Mixed Workflow
    # ----------------------------
    pipe = AgentXPipe(
        agents=[
            research_agent,
            [blog_agent, linkedin_agent],   # router decides which to run
            editor_agent
        ],
        router=router,
        workflow_store=False
    )

    task = "Create digital marketing content about Agentic AI"

    result = await pipe.flow(
        query_instruction=task
    )

    end_time = time.time()

    print("\n==============================")
    print("🎯 FINAL RESULT")
    print("==============================\n")
    print(result)

    print(f"\n⏱ Total Execution Time: {end_time - start_time:.2f} seconds")


if __name__ == "__main__":
    asyncio.run(main())