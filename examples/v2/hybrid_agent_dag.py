import asyncio
import logging

from superagentx.agent import Agent
from superagentx.handler.ai import AIHandler
from superagentx.handler.task.greetings.welcome_handler import WelcomeHandler
from superagentx.llm import LLMClient
from superagentx.prompt import PromptTemplate
from superagentx.task_engine import TaskEngine

# Import your newly designed stateful DAG orchestrator classes
# (Ensure these classes are imported correctly from your codebase)
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
    print("🚀 Welcome to Gold Rates & Greeting Pipeline (DAG Powered)")

    # 1. Initialize LLM Client
    llm_client = LLMClient(
        llm_config={
            "model": "gemini/gemini-2.5-flash"
        }
    )

    ai_handler = AIHandler(llm=llm_client)

    # ----------------------------------
    # 2. Setup Gold Rate Analyst Agent
    # ----------------------------------
    gold_rate_agent = Agent(
        name="Gold_Rate_Agent",  # Explicitly name your node for the graph
        goal="Generate Gold Rates",
        role="Gold Rate Analyst",
        llm=llm_client,
        prompt_template=PromptTemplate(system_message="""
        Generate today's gold rates in JSON.

        {
            "24K": {
                "per_gram": "",
                "per_10_gram": ""
            },
            "22K": {
                "per_gram": "",
                "per_10_gram": ""
            },
            "18K": {
                "per_gram": "",
                "per_10_gram": ""
            }
        }
        """),
        tool=ai_handler,
    )

    oil_agent = Agent(
        name="Oil_Rate_Agent",  # Explicitly name your node for the graph
        goal="Generate Petrol / Diesel Rates",
        role="Petrol / Diesel Rate Analyst",
        llm=llm_client,
        prompt_template=PromptTemplate(system_message="""
           Generate Dummy Petrol Diesel rates in JSON.

           {
               "Petrol": {
                   "per_litre": "",
                   "per_10_litre": ""
               },
               "Diesel": {
                   "per_litre": "",
                   "per_10_litre": ""
               },
           }
           """),
        tool=ai_handler,
        human_approval=False
    )

    # ----------------------------------
    # 3. Setup Greeting Task Agent
    # ----------------------------------
    handler = WelcomeHandler(first_name="John", last_name="Doe")

    engine = TaskEngine(
        handler=handler,
        instructions=[
            {"send_greeting": {"message": "$prev_result"}}
        ]
    )

    task_agent = Agent(
        name="Greeting_Task_Agent",  # Explicitly name your node for the graph
        engines=[engine]
    )

    # =====================================================================
    # 4. Define Blueprint and Node Connections (The Topological Map)
    # =====================================================================
    blueprint = WorkflowBlueprint(name="Gold_Rates_Greeting_Workflow")

    # Register both nodes
    blueprint.add_node(gold_rate_agent)
    blueprint.add_node(oil_agent)
    blueprint.add_node(task_agent)

    # Establish sequence path: Gold_Rate_Agent runs first -> Output feeds into Greeting_Task_Agent
    blueprint.add_path(["Gold_Rate_Agent", "Oil_Rate_Agent"], "Greeting_Task_Agent")

    # =====================================================================
    # 5. Instantiate State Persistence Store & DAG Engine
    # =====================================================================
    store = InMemoryStore()

    dag_engine = AgentXDag(
        blueprint=blueprint,
        store=store,
        stop_if_goal_not_satisfied=False,
        workflow_store=True
    )

    # Unique identifier tracking this specific execution instance
    run_id = "run_gold_rate_greeting_101"
    task_instruction = ""

    # =====================================================================
    # 6. Execute DAG Pipeline
    # =====================================================================
    print(f"\n⚡ Starting DAG Execution: [{run_id}]...")

    final_states = await dag_engine.execute(
        run_id=run_id,
        initial_ctx={
            "query_instruction": task_instruction,
            "pre_result": []
        }
    )

    # =====================================================================
    # 7. Print Executed Node Results
    # =====================================================================
    print("\n📊 Pipeline Execution Complete!")
    for node, state in final_states.items():
        print(f" - {node}: {state.value}")

    checkpoint = store.load(run_id)
    if checkpoint:
        print("\n=======================================================")
        print("🟡 [OUTPUT 1] Gold Rates Output:")
        print(checkpoint.results.get("Gold_Rate_Agent"))
        print("🟡 [OUTPUT 2] Oil Rates Output:")
        print(checkpoint.results.get("Oil_Rate_Agent"))
        print("\n🟢 [OUTPUT 3] Greeting Message Output:")
        print(checkpoint.results.get("Greeting_Task_Agent"))
        print("=======================================================")


if __name__ == "__main__":
    asyncio.run(main())