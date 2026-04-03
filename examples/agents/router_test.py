import asyncio

from superagentx.agent import Agent
from superagentx.agentxpipe import AgentXPipe
from superagentx.handler.ai import AIHandler
from superagentx.llm import LLMClient
from superagentx.prompt import PromptTemplate
from superagentx.router.router_engine import RouterEngine


async def main():
    print("Testing Parallel Math Agents in SuperAgentX")

    # LLM Config
    llm_config = {"model": "gemini/gemini-2.5-flash"}
    llm_client = LLMClient(llm_config=llm_config)

    handler = AIHandler(llm=llm_client)

    # -----------------------------
    # Math Agents (PARALLEL)
    # -----------------------------

    add_agent = Agent(
        goal="Perform addition",
        role="Addition Agent",
        tool=handler,
        llm=llm_client,
        prompt_template=PromptTemplate(
            system_message="You are a math agent. Perform addition for given numbers and return result clearly."
        ),
        max_retry=1
    )

    sub_agent = Agent(
        goal="Perform subtraction",
        role="Subtraction Agent",
        tool=handler,
        llm=llm_client,
        prompt_template=PromptTemplate(
            system_message="You are a math agent. Perform subtraction for given numbers and return result clearly."
        ),
        max_retry=1
    )

    mul_agent = Agent(
        goal="Perform multiplication",
        role="Multiplication Agent",
        tool=handler,
        llm=llm_client,
        prompt_template=PromptTemplate(
            system_message="You are a math agent. Perform multiplication for given numbers and return result clearly."
        ),
        max_retry=1
    )

    div_agent = Agent(
        goal="Perform division",
        role="Division Agent",
        tool=handler,
        llm=llm_client,
        prompt_template=PromptTemplate(
            system_message="You are a math agent. Perform division for given numbers and return result clearly. Handle divide-by-zero."
        ),
        max_retry=1
    )

    # -----------------------------
    # Summary Agent (SEQUENTIAL)
    # -----------------------------

    summary_agent = Agent(
        goal="Summarise all math results",
        role="Summary Agent",
        tool=handler,
        llm=llm_client,
        prompt_template=PromptTemplate(
            system_message="""
You will receive results from multiple math agents.
Summarise and display clearly in bullet points like:

- Addition Result: X
- Subtraction Result: Y
- Multiplication Result: Z
- Division Result: W

YOU SHOULD NOT PERFORM ANY MATHEMATICAL CALCULATIONS. DISPLAY ONLY
"""
        ),
        max_retry=1
    )

    # ----------------------------
    # Router Setup
    # ----------------------------
    router = RouterEngine(
        llm=llm_client,
        mode="llm"
    )
    # -----------------------------
    # PIPELINE
    # -----------------------------
    pipe = AgentXPipe(
        agents=[
            [add_agent, sub_agent, mul_agent, div_agent],  # PARALLEL
            summary_agent                                 # SEQUENTIAL
        ],
        router=router,
        workflow_store=False
    )

    # Input task
    task = "Sum of numbers 20 and 20"

    result = await pipe.flow(query_instruction=task)

    print("\nFinal Output:")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())