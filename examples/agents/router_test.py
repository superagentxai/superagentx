import asyncio

from superagentx.agent import Agent
from superagentx.agentxpipe import AgentXPipe
from superagentx.handler.ai import AIHandler
from superagentx.llm import LLMClient
from superagentx.prompt import PromptTemplate
from superagentx.router.router_engine import RouterEngine


async def main():
    print("Testing Teacher + Parallel Math Agents in SuperAgentX")

    # -----------------------------
    # LLM Config
    # -----------------------------
    llm_config = {"model": "gemini/gemini-2.5-flash"}
    llm_client = LLMClient(llm_config=llm_config)

    handler = AIHandler(llm=llm_client)

    # -----------------------------
    # TEACHER AGENT (NEW)
    # -----------------------------
    teacher_agent = Agent(
        name="teacher_agent",
        agent_id="000",
        goal="Create a structured math test for other agents",
        role="Math Teacher",
        tool=handler,
        llm=llm_client,
        prompt_template=PromptTemplate(
            system_message="""
You are a Math Teacher.

1. Randomly generate Maths test. Give Home work in Addition or Subtract or Multiplication or Division. Not all expressions.
2. Create a structured math test for agents:
   - Addition
   - Subtraction
   - Multiplication
   - Division

Return instructions clearly like:

Addition: <expression>
Subtraction: <expression>
Multiplication: <expression>
Division: <expression>

Only generate any TWO Expressions. DO NOT solve it.
"""
        ),
        max_retry=1
    )

    # -----------------------------
    # Math Agents (PARALLEL)
    # -----------------------------

    add_agent = Agent(
        name="add_agent",
        agent_id="001",
        goal="Perform addition",
        role="Addition Agent",
        tool=handler,
        llm=llm_client,
        prompt_template=PromptTemplate(
            system_message="""
You are an Addition Agent.
Extract ONLY the addition task and solve it.
Return only the result.
"""
        ),
        max_retry=1
    )

    sub_agent = Agent(
        name="sub_agent",
        agent_id="002",
        goal="Perform subtraction",
        role="Subtraction Agent",
        tool=handler,
        llm=llm_client,
        prompt_template=PromptTemplate(
            system_message="""
You are a Subtraction Agent.
Extract ONLY the subtraction task and solve it.
Return only the result.
"""
        ),
        max_retry=1
    )

    mul_agent = Agent(
        name="mul_agent",
        agent_id="003",
        goal="Perform multiplication",
        role="Multiplication Agent",
        tool=handler,
        llm=llm_client,
        prompt_template=PromptTemplate(
            system_message="""
You are a Multiplication Agent.
Extract ONLY the multiplication task and solve it.
Return only the result.
"""
        ),
        max_retry=1
    )

    div_agent = Agent(
        name="div_agent",
        agent_id="004",
        goal="Perform division",
        role="Division Agent",
        tool=handler,
        llm=llm_client,
        prompt_template=PromptTemplate(
            system_message="""
You are a Division Agent.
Extract ONLY the division task and solve it.
Handle divide-by-zero safely.
Return only the result.
"""
        ),
        max_retry=1
    )

    # -----------------------------
    # Summary Agent (SEQUENTIAL)
    # -----------------------------
    summary_agent = Agent(
        name="summary_agent",
        agent_id="005",
        goal="Summarise all math results",
        role="Summary Agent",
        tool=handler,
        llm=llm_client,
        prompt_template=PromptTemplate(
            system_message="""
You will receive results from multiple math agents.

Summarise clearly:

- Addition Result: X
- Subtraction Result: Y
- Multiplication Result: Z
- Division Result: W

DO NOT perform calculations. Just format.
"""
        ),
        max_retry=1
    )

    # ----------------------------
    # Router
    # ----------------------------
    router = RouterEngine(
        llm=llm_client,
        mode="llm"
    )

    # -----------------------------
    # PIPELINE (UPDATED)
    # -----------------------------
    pipe = AgentXPipe(
        agents=[
            teacher_agent,                              # Step 1 (Sequential)
            [add_agent, sub_agent, mul_agent, div_agent],  # Step 2 (Parallel)
            summary_agent                              # Step 3 (Sequential)
        ],
        router=router,
        workflow_store=False
    )

    # -----------------------------
    # Input Task
    # -----------------------------
    task = "Execute the flow"

    result = await pipe.flow(query_instruction=task)

    print("\nFinal Output:")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())