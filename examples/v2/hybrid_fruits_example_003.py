import asyncio

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
    NodeState
)

# Enable SuperAgentX verbose mode
from superagentx.config import is_verbose_enabled

is_verbose_enabled()


async def main():
    print("🚀 Running Tiny Multi-Tier Test Scenario")

    # 1. Initialize LLM Client
    llm_client = LLMClient(llm_config={"model": "gemini/gemini-2.5-flash", "llm_type": "litellm"})
    ai_handler = AIHandler(llm=llm_client)
    prompt_template = PromptTemplate()

    # =====================================================================
    # LAYER 1: Parallel Source Words (Under 10-15 Words)
    # =====================================================================
    word_a_agent = Agent(
        name="Apple_Agent",
        goal="Output exactly: Do not write anything else.",
        role="Apple Spec ",
        llm=llm_client,
        prompt_template=PromptTemplate(system_message="Return ONLY this text - 'Apple is a crispy sweet red fruit'."),
        tool=ai_handler
    )

    word_b_agent = Agent(
        name="Banana_Agent",
        goal="You're Banana Expert. Output exactly: Do not write anything else. ",
        role="Banana Spec ",
        llm=llm_client,
        prompt_template=PromptTemplate(system_message="Return ONLY this text - 'Banana is a soft yellow tropical fruit.'"),
        tool=ai_handler
    )

    # =====================================================================
    # LAYER 2: Parallel Convergence Layer (Under 10-15 Words)
    # =====================================================================
    joiner_agent = Agent(
        name="Word_Joiner_Agent",
        goal="Combine the names of the upstream fruits into a sentence under 10 words.",
        role="Text Linker",
        llm=llm_client,
        prompt_template=prompt_template,
        tool=ai_handler
    )

    # =====================================================================
    # LAYER 3: Terminal Automation Node
    # =====================================================================
    handler = WelcomeHandler(first_name="John", last_name="Doe")
    engine = TaskEngine(
        handler=handler,
        instructions=[{"send_greeting": {"message": "$prev_result"}}]
    )
    task_agent = Agent(
        name="Final_Greeting_Agent",
        engines=[engine]
    )

    # =====================================================================
    # 📐 BLUEPRINT STRUCTURAL TOPOLOGY GRAPH BINDINGS
    # =====================================================================
    blueprint = WorkflowBlueprint(name="Tiny_Fruit_Pipeline")

    # Register all nodes
    blueprint.add_node(word_a_agent)
    blueprint.add_node(word_b_agent)
    blueprint.add_node(joiner_agent)
    blueprint.add_node(task_agent)

    # Map the flow path hierarchy
    blueprint.add_path(["Apple_Agent", "Banana_Agent"], "Word_Joiner_Agent")
    blueprint.add_path("Word_Joiner_Agent", "Final_Greeting_Agent")


    store = InMemoryStore()
    dag_engine = AgentXDag(
        blueprint=blueprint,
        store=store,
        stop_on_node_failure=True,
        workflow_store=True
    )

    run_id = "tiny_hierarchical_run_101"

    final_states = await dag_engine.execute(
        run_id=run_id,
        initial_ctx={
            "query_instruction": "Execute short phrase extraction test.",
            "pre_result": []
        }
    )

    for node, state in final_states.items():
        print(f" - Node: [{node:<22}] State: {state.value}")

    checkpoint = store.load(run_id)
    if checkpoint:

        # print("[Word_A_Agent]:", dag_engine._extract_output(checkpoint.results.get("Word_A_Agent")))
        # print("[Word_B_Agent]:", dag_engine._extract_output(checkpoint.results.get("Word_B_Agent")))
        # print("[Word_Joiner_Agent Concatenation Check]:")
        # print(dag_engine._extract_output(checkpoint.results.get("Word_Joiner_Agent")))
        print(" [Final_Greeting_Agent]:", dag_engine._extract_output(checkpoint.results.get("Final_Greeting_Agent")))


if __name__ == "__main__":
    asyncio.run(main())