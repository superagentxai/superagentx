import asyncio

from superagentx.agent import Agent
from superagentx.agentxpipe import AgentXPipe
from superagentx.browser_engine import BrowserEngine
from superagentx.handler.ai import AIHandler
from superagentx.handler.mcp import MCPHandler
from superagentx.llm import LLMClient
from superagentx.prompt import PromptTemplate
from superagentx.engine import Engine


async def main():

    # ------------------------------------------------------------
    # LLM
    # ------------------------------------------------------------

    llm_client = LLMClient(
        llm_config={
            "model": "gemini/gemini-2.5-flash",
        }
    )

    prompt_template = PromptTemplate()

    # ------------------------------------------------------------
    # Engines
    # ------------------------------------------------------------

    browser_engine = BrowserEngine(
        llm=llm_client,
        prompt_template=prompt_template,
    )

    mcp_handler = MCPHandler(command="python", mcp_args=["-m", "mcp_server_reddit"])
    reddit_engine = Engine(handler=mcp_handler, llm=llm_client,
                           prompt_template=prompt_template)


    ai_engine = AIHandler(
        llm=llm_client
    )

    # ------------------------------------------------------------
    # Agent 1
    # Browser Agent
    # ------------------------------------------------------------

    fifa_agent = Agent(
        name="FIFA_Browser_Agent",
        role="Football News Analyst",
        goal="Find the latest FIFA football results and important football news.",
        llm=llm_client,
        prompt_template=PromptTemplate(
            system_message="""
Use the browser to search for:

- Latest FIFA football match results
- Important football headlines
- Upcoming major matches

Return a concise summary.
"""
        ),
        engines=[browser_engine],
    )

    # ------------------------------------------------------------
    # Agent 2
    # Reddit Agent
    # ------------------------------------------------------------

    cricket_agent = Agent(
        name="Cricket_Reddit_Agent",
        role="Cricket Community Analyst",
        goal="List top Cricket Trends",
        llm=llm_client,
        prompt_template=PromptTemplate(
            system_message="""
Search Reddit for:

- Latest cricket discussions
- Match highlights
- Trending cricket news
- Community opinions

Return a concise summary.
"""
        ),
        engines=[reddit_engine],
    )

    apple_agent = Agent(
        name="Apple_Agent",
        role="Apple Expert",
        goal="Return only the requested sentence.",
        llm=llm_client,
        prompt_template=PromptTemplate(
            system_message="Return ONLY: Apple is a crispy sweet red fruit."
        ),
        tool=ai_engine,
    )

    # ------------------------------------------------------------
    # Agent 3
    # AI Summarizer
    # ------------------------------------------------------------

    summary_agent = Agent(
        name="Sports_Summary_Agent",
        role="Sports News Editor",
        goal="Create one sports briefing from all upstream agent outputs.",
        llm=llm_client,
        prompt_template=PromptTemplate(
            system_message="""
You will receive outputs from multiple upstream agents.

Create a single sports briefing containing:

• FIFA Updates
• Cricket Updates
• Overall Highlights

Keep the response under 250 words.
"""
        ),
        tool=ai_engine,
    )

    # ------------------------------------------------------------
    # AgentXPipe
    # ------------------------------------------------------------

    pipe = AgentXPipe(
        agents=[
            [
                apple_agent,
                cricket_agent
            ],
            summary_agent
        ],
        workflow_store=True,
        stop_on_node_failure=True,
    )

    # ------------------------------------------------------------
    # Execute Workflow
    # ------------------------------------------------------------


    checkpoint = await pipe.flow(query_instruction=" Execute")
    # ------------------------------------------------------------
    # Results
    # ------------------------------------------------------------

    print("\n========== Workflow States ==========")

    for node, state in checkpoint.states.items():
        print(f"{node:<30} {state.value}")

    print("\n========== Agent Outputs ==========")

    for node, result in checkpoint.results.items():
        print(f"\n{'=' * 60}")
        print(node)
        print("=" * 60)
        print(result)


if __name__ == "__main__":
    asyncio.run(main())