import asyncio
import logging

from superagentx.agent import Agent
from superagentx.handler.ai import AIHandler
from superagentx.handler.simple_math import MathToolHandler
from superagentx.llm import LLMClient
from superagentx.prompt import PromptTemplate

# Import your stateful DAG orchestrator classes
from superagentx.agentxdag import (
    AgentXDag,
    WorkflowBlueprint,
    InMemoryStore,
    NodeState
)

# Enable SuperAgentX verbose mode
from superagentx.config import is_verbose_enabled

is_verbose_enabled()


async def main():
    print("🚀 Running Multi-Agent Aggregation (DAG Architecture)")

    # --- STEP 1: INITIALIZE LLM CLIENTS & HANDLERS ---
    llm_config = {"model": "gemini/gemini-2.5-flash", "llm_type": "litellm"}
    llm_client = LLMClient(llm_config=llm_config)
    math_tool = MathToolHandler()
    summary_handler = AIHandler(llm=llm_client)
    prompt_template = PromptTemplate()

    # --- STEP 2: DEFINE THE THREE AGENTS ---

    # --- STEP 2: DEFINE THE THREE AGENTS WITH EXPLICIT TEXT-MATH GOALS ---

    # Agent 1: Forced to process addition as direct output text
    # Agent 1 has access to the math tool handler to compute addition
    addition_agent = Agent(
        name="Addition_Agent",
        goal="Extract the two numbers from the user input as numeric and use the calculate_addition tool to compute their sum.",
        role="Addition Specialist",
        llm=llm_client,
        prompt_template=prompt_template,
        tool=math_tool,  # Pass the tool handler containing our custom tool
        max_retry=2
    )

    # Agent 2 has access to the math tool handler to compute multiplication
    multiplication_agent = Agent(
        name="Multiplication_Agent",
        goal="Extract the two numbers from the user input and do ONLY multiplications by using the calculate_multiplication tool to compute their product.",
        role="Multiplication Specialist",
        llm=llm_client,
        prompt_template=prompt_template,
        tool=math_tool,  # Pass the tool handler containing our custom tool
        max_retry=2
    )

    # Agent 3: Merges the text elements together cleanly
    summary_agent = Agent(
        name="Summary_Synthesizer_Agent",
        goal=(
            "Review the text addition and multiplication equations provided in the context blocks. "
            "Compile them into a clean, final consolidated mathematical calculation overview markdown report."
        ),
        role="Lead Synthesizer",
        llm=llm_client,
        prompt_template=prompt_template,
        tool=summary_handler,
        max_retry=1
    )

    # --- STEP 3: CONSTRUCT THE BLUEPRINT TOPOLOGY ---
    store = InMemoryStore()
    blueprint = WorkflowBlueprint("Math Operations Aggregator Blueprint")

    # 1. Register all nodes into the pipeline graph landscape
    # blueprint.add_node(addition_agent, name="Addition_Agent")
    blueprint.add_node(multiplication_agent, name="Multiplication_Agent")
    blueprint.add_node(summary_agent, name="Summary_Synthesizer_Agent")

    # 2. Draw the convergence path maps
    # Both Addition_Agent and Multiplication_Agent run simultaneously in parallel.
    # Summary_Synthesizer_Agent will wait automatically until BOTH have finished.
    blueprint.add_path(["Multiplication_Agent"], "Summary_Synthesizer_Agent")

    # --- STEP 4: INITIALIZE THE DAG RUNTIME ENGINE ---
    dag_engine = AgentXDag(
        blueprint=blueprint,
        store=store,
        stop_on_node_failure=True
    )

    run_id = "wf_math_aggregation_2026"

    # Global instruction prompt provided to the root nodes
    initial_input = {
        "query_instruction": "Please compute addition and multiplication operations using the baseline values 12 and 8."
    }

    # --- STEP 5: EXECUTE THE WORKFLOW PIPELINE ---
    print("\n▶️  Executing Math Workflow Engine...")
    final_states = await dag_engine.execute(run_id=run_id, initial_ctx=initial_input)

    # --- STEP 6: TELEMETRY RESULTS LOGS ---
    print("\n" + "=" * 60)
    print("📊 Pipeline Execution Lifecycle Status Matrix:")
    print("=" * 60)
    for node_name, state in final_states.items():
        print(f"Node: [{node_name:<30}] -> Lifecycle State: {state.value}")

    # --- STEP 7: COMPONENT DATA STREAM INSPECTION & PRINTING ---
    print("\n" + "=" * 60)
    print("📥 RETRIEVING GENERATED CONTENT FROM STORAGE")
    print("=" * 60)

    checkpoint = store.load(run_id)
    if checkpoint:
        # Extract and print individual outputs if desired
        raw_add = checkpoint.results.get("Addition_Agent")
        raw_mul = checkpoint.results.get("Multiplication_Agent")
        raw_sum = checkpoint.results.get("Summary_Synthesizer_Agent")

        print("\n➕ [Addition_Agent Output]:")
        print(dag_engine._extract_output(raw_add))

        print("\n✖️ [Multiplication_Agent Output]:")
        print(dag_engine._extract_output(raw_mul))

        print("\n📝 [Summary_Synthesizer_Agent Final Report]:")
        print(dag_engine._extract_output(raw_sum))
    else:
        print("❌ Error: Workflow checkpoint data missing from storage lifecycle.")

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())