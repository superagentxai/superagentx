import asyncio
import logging

from superagentx.agent import Agent
from superagentx.handler.ai import AIHandler
from superagentx.handler.task.greetings.welcome_handler import WelcomeHandler
from superagentx.llm import LLMClient
from superagentx.prompt import PromptTemplate
from superagentx.task_engine import TaskEngine

# Import your stateful DAG orchestrator classes
from superagentx.agentxdag import (
    AgentXDag,
    WorkflowBlueprint,
    InMemoryStore,
    RunCheckpoint,
    NodeState
)

# Enable SuperAgentX verbose mode
from superagentx.config import is_verbose_enabled

is_verbose_enabled()


async def main():
    print("🚀 Running Multi-Tier Complex Hierarchy Test on AgentXDag Engine")

    # 1. Initialize LLM Client
    llm_client = LLMClient(llm_config={"model": "gemini/gemini-2.5-flash", "llm_type": "litellm"})
    ai_handler = AIHandler(llm=llm_client)
    prompt_template = PromptTemplate()

    # =====================================================================
    # LAYER 1: Parallel Commodity Raw Feeder Agents
    # =====================================================================
    gold_rate_agent = Agent(
        name="Gold_Rate_Agent",
        goal="Generate today's raw gold rates in JSON format for 24K, 22K, and 18K per gram.",
        role="Gold Analyst",
        llm=llm_client,
        prompt_template=prompt_template,
        tool=ai_handler
    )

    oil_agent = Agent(
        name="Oil_Rate_Agent",
        goal="Generate today's raw baseline Petrol and Diesel fuel pricing per litre in JSON format.",
        role="Oil Analyst",
        llm=llm_client,
        prompt_template=prompt_template,
        tool=ai_handler
    )

    crypto_agent = Agent(
        name="Crypto_Rate_Agent",
        goal="Generate today's baseline top cryptocurrency rates (BTC, ETH, SOL) in JSON format.",
        role="Crypto Analyst",
        llm=llm_client,
        prompt_template=prompt_template,
        tool=ai_handler
    )

    # =====================================================================
    # LAYER 2: Context Aggregation Layer (Simulates human authorization check)
    # =====================================================================
    aggregator_agent = Agent(
        name="Market_Data_Aggregator_Agent",
        goal=(
            "Review the text segments compiled by the Gold, Oil, and Crypto agents. "
            "Combine them into a single clean integrated Market Data Summary Table."
        ),
        role="Lead Consolidation Editor",
        llm=llm_client,
        prompt_template=prompt_template,
        tool=ai_handler
    )

    # =====================================================================
    # LAYER 3: Downstream Calculation Processing Node
    # =====================================================================
    converter_agent = Agent(
        name="Currency_Converter_Agent",
        goal=(
            "Take the integrated Market Data Summary Table from the aggregator. "
            "Create an alternative section converted directly into Euros (€) based on a benchmark standard rate."
        ),
        role="Financial Exchange Expert",
        llm=llm_client,
        prompt_template=prompt_template,
        tool=ai_handler
    )

    # =====================================================================
    # LAYER 4: Final Processing Task Automation Node
    # =====================================================================
    handler = WelcomeHandler(first_name="John", last_name="Doe")
    engine = TaskEngine(
        handler=handler,
        instructions=[{"send_greeting": {"message": "$prev_result"}}]
    )
    task_agent = Agent(
        name="Greeting_Task_Agent",
        engines=[engine]
    )

    # =====================================================================
    # 📐 BLUEPRINT STRUCTURAL TOPOLOGY GRAPH BINDINGS
    # =====================================================================
    blueprint = WorkflowBlueprint(name="Complex_MultiTier_Commodities_Pipeline")

    # 1. Register all nodes into the pipeline schema map
    blueprint.add_node(gold_rate_agent)
    blueprint.add_node(oil_agent)
    blueprint.add_node(crypto_agent)

    # Setting approval_required=True blocks execution here until approved, testing the PAUSE capability
    blueprint.add_node(aggregator_agent, approval_required=False)
    blueprint.add_node(converter_agent)
    blueprint.add_node(task_agent)

    # 2. Map structural multi-parent convergence path arrays
    # Tier 1 (Parallel roots) -> Converges at Tier 2
    blueprint.add_path(["Gold_Rate_Agent", "Oil_Rate_Agent", "Crypto_Rate_Agent"], "Market_Data_Aggregator_Agent")

    # Tier 2 -> Flows into Tier 3
    blueprint.add_path("Market_Data_Aggregator_Agent", "Currency_Converter_Agent")

    # Tier 3 -> Ends at Tier 4
    blueprint.add_path("Currency_Converter_Agent", "Greeting_Task_Agent")

    # =====================================================================
    # 🚀 ENGINE RUNTIME INSTANTIATION AND DISPATCH
    # =====================================================================
    store = InMemoryStore()
    dag_engine = AgentXDag(
        blueprint=blueprint,
        store=store,
        stop_on_node_failure=True,
        workflow_store=True
    )

    run_id = "complex_hierarchical_run_2026"
    print(f"\n⚡ Dispatching Complex DAG Pipeline Execution: [{run_id}]...")

    final_states = await dag_engine.execute(
        run_id=run_id,
        initial_ctx={
            "query_instruction": "Generate market matrix data sets for terminal dashboard review.",
            "pre_result": []
        }
    )

    # =====================================================================
    # 📊 LIFE-CYCLE MONITORING REPORT
    # =====================================================================
    print("\n" + "=" * 60)
    print("📊 Pipeline Node State Verification Matrix:")
    print("=" * 60)
    for node, state in final_states.items():
        print(f" - Node: [{node:<30}] State: {state.value}")

    checkpoint = store.load(run_id)
    if checkpoint:
        print("\n" + "=" * 60)
        print("📝 STRUCTURAL DATA STREAM EXTRACTION CONSOLE LOGS")
        print("=" * 60)

        # Test extraction of Parallel Tier 1 logs
        print("\n🟡 [Tier 1] Crypto Rates Snippet:")
        print(dag_engine._extract_output(checkpoint.results.get("Crypto_Rate_Agent")))

        # Test extraction of Merged Convergence Tier 2 logs
        print("\n🟠 [Tier 2] Aggregator Combined Output:")
        print(dag_engine._extract_output(checkpoint.results.get("Market_Data_Aggregator_Agent")))

        # Test extraction of Final Processing Terminal Node logs
        print("\n🟢 [Tier 4] Terminal Greeting Automation Result:")
        print(dag_engine._extract_output(checkpoint.results.get("Greeting_Task_Agent")))
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())