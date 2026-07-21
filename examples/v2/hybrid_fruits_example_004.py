import asyncio

from superagentx.agent import Agent
from superagentx.agentxpipe import AgentXPipe
from superagentx.config import is_verbose_enabled
from superagentx.handler.ai import AIHandler
from superagentx.handler.task.greetings.welcome_handler import WelcomeHandler
from superagentx.llm import LLMClient
from superagentx.prompt import PromptTemplate
from superagentx.task_engine import TaskEngine

is_verbose_enabled()


async def main():
    print("🚀 Running Tiny Multi-Tier Test Scenario")

    # ------------------------------------------------------------------
    # LLM
    # ------------------------------------------------------------------

    llm_client = LLMClient(
        llm_config={
            "model": "gemini/gemini-2.5-flash",
            "llm_type": "litellm",
        }
    )

    ai_handler = AIHandler(llm=llm_client)

    # ------------------------------------------------------------------
    # Layer 1 (Parallel)
    # ------------------------------------------------------------------

    apple_agent = Agent(
        name="Apple_Agent",
        role="Apple Expert",
        goal="Return only the requested sentence.",
        llm=llm_client,
        prompt_template=PromptTemplate(
            system_message="Return ONLY: Apple is a crispy sweet red fruit."
        ),
        tool=ai_handler,
    )

    banana_agent = Agent(
        name="Banana_Agent",
        role="Banana Expert",
        goal="Return only the requested sentence.",
        llm=llm_client,
        prompt_template=PromptTemplate(
            system_message="Return ONLY: Banana is a soft yellow tropical fruit."
        ),
        tool=ai_handler,
    )

    # ------------------------------------------------------------------
    # Layer 2
    # ------------------------------------------------------------------

    joiner_agent = Agent(
        name="Word_Joiner_Agent",
        role="Text Summarizer",
        goal="Combine upstream outputs into one short sentence.",
        llm=llm_client,
        prompt_template=PromptTemplate(
            system_message="""
You will receive outputs from multiple upstream agents.

Merge them into one natural sentence.

Maximum 15 words.
"""
        ),
        tool=ai_handler,
    )

    # ------------------------------------------------------------------
    # Layer 3 (Automation)
    # ------------------------------------------------------------------

    handler = WelcomeHandler(
        first_name="John",
        last_name="Doe",
    )

    engine = TaskEngine(
        handler=handler,
        instructions=[
            {
                "send_greeting": {
                    "message": "$prev_result"
                }
            }
        ],
    )

    final_agent = Agent(
        name="Final_Greeting_Agent",
        engines=[engine],
    )

    # ------------------------------------------------------------------
    # AgentXPipe
    # ------------------------------------------------------------------

    pipe = AgentXPipe(
        agents=[
            [
                apple_agent,
                banana_agent,
            ],
            joiner_agent,
            final_agent,
        ],
        workflow_store=True,
        stop_on_node_failure=True,
    )

    checkpoint = await pipe.flow(
        query_instruction="Execute short phrase extraction test."
    )

    # ------------------------------------------------------------------
    # Results
    # ------------------------------------------------------------------

    print("\nWorkflow States")

    for node, state in checkpoint.states.items():
        print(f" - {node:<25} {state.value}")

    print("\nOutputs")

    for node, result in checkpoint.results.items():
        print(f"\n[{node}]")
        print(result)


if __name__ == "__main__":
    asyncio.run(main())