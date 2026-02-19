import asyncio
import time

from superagentx.agent import Agent
from superagentx.agentxpipe import AgentXPipe
from superagentx.handler.ai import AIHandler
from superagentx.llm import LLMClient
from superagentx.prompt import PromptTemplate


async def main():
    print("🚀 SuperAgentX Mixed Sequential + Parallel Demo")

    start_time = time.time()

    # LLM Config
    llm_config = {"model": "gemini/gemini-2.5-flash"}
    llm_client = LLMClient(llm_config=llm_config)

    handler = AIHandler(llm=llm_client)

    # ----------------------------
    # Research Agent (Sequential)
    # ----------------------------
    research_agent = Agent(
        goal="Research and outline key points about Agentic AI in digital marketing",
        role="Market Research Analyst",
        tool=handler,
        llm=llm_client,
        prompt_template=PromptTemplate(),
        max_retry=1
    )

    # ----------------------------
    # Blog Content Agent (Parallel)
    # ----------------------------
    blog_agent = Agent(
        goal="Generate a detailed blog article based on the research",
        role="Professional Blog Writer",
        tool=handler,
        llm=llm_client,
        prompt_template=PromptTemplate(),
        max_retry=1
    )

    # ----------------------------
    # LinkedIn Post Agent (Parallel)
    # ----------------------------
    linkedin_agent = Agent(
        goal="Create an engaging LinkedIn post based on the research",
        role="Social Media Strategist",
        tool=handler,
        llm=llm_client,
        prompt_template=PromptTemplate(),
        max_retry=1
    )

    # ----------------------------
    # 4️⃣ Final Editor Agent (Sequential)
    # ----------------------------
    editor_agent = Agent(
        goal="Combine blog and LinkedIn content into a cohesive final output",
        role="Senior Content Editor",
        tool=handler,
        llm=llm_client,
        prompt_template=PromptTemplate(),
        max_retry=1
    )

    # Mixed Workflow:
    # Step 1 → research_agent (Sequential)
    # Step 2 → blog_agent + linkedin_agent (Parallel)
    # Step 3 → editor_agent (Sequential)
    pipe = AgentXPipe(
        agents=[
            research_agent,
            [blog_agent, linkedin_agent],
            editor_agent
        ],
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
