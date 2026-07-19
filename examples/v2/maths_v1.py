import asyncio
import logging

from superagentx.agent import Agent
from superagentx.handler.base import BaseHandler
from superagentx.handler.decorators import tool
from superagentx.handler.ai import AIHandler
from superagentx.handler.task.general.dummy_handler import DummyHandler
from superagentx.llm import LLMClient
from superagentx.prompt import PromptTemplate
from superagentx.agentxdag import AgentXDag, WorkflowBlueprint, InMemoryStore
from superagentx.task_engine import TaskEngine

logger = logging.getLogger("SuperAgentX.DAG")
# =====================================================================
# 🧩 STEP 1: ISOLATE THE HANDLERS TO PREVENT LLM CONFUSION
# =====================================================================

class AdditionToolHandler(BaseHandler):
    """Provides ONLY addition capabilities."""

    def __init__(self):
        super().__init__()

    @tool
    async def calculate_addition(self, a: float, b: float) -> str:
        """
        Executes arithmetic addition on two numerical values.

        Args:
            a (float): The first value.
            b (float): The second value.
        """
        return f"Addition Calculation: {a} + {b} = {a + b}"


class MultiplicationToolHandler(BaseHandler):
    """Provides ONLY multiplication capabilities. Addition is physically impossible here."""

    def __init__(self):
        super().__init__()

    @tool
    async def calculate_multiplication(self, a: float, b: float) -> str:
        """
        Executes arithmetic multiplication on two numerical values.

        Args:
            a (float): The first factor value.
            b (float): The second factor value.
        """
        return f"Multiplication Calculation: {a} * {b} = {a * b}"


async def main():
    llm_config = {"model": "gemini/gemini-2.5-flash", "llm_type": "litellm"}
    llm_client = LLMClient(llm_config=llm_config)
    prompt_template = PromptTemplate()

    # 2. Instantiate isolated tools
    addition_tool = AdditionToolHandler()
    multiplication_tool = MultiplicationToolHandler()
    summary_handler = AIHandler(llm=llm_client)

    # =====================================================================
    # 🤖 STEP 2: ASSIGN STRICTLY ISOLATED TOOLS TO AGENTS
    # =====================================================================

    addition_agent = Agent(
        name="Addition_Agent",
        goal="Extract numbers from user as numeric input and use the calculate_addition tool to compute their sum.",
        role="Addition Specialist",
        llm=llm_client,
        prompt_template=prompt_template,
        tool=addition_tool,  # Can only see addition
        max_retry=2
    )

    multiplication_agent = Agent(
        name="Multiplication_Agent",
        goal="Extract numbers from user as float input and use the calculate_multiplication tool to compute their product.",
        role="Multiplication Specialist",
        llm=llm_client,
        prompt_template=prompt_template,
        tool=multiplication_tool,  # Physically impossible to call addition!
        max_retry=2
    )

    dummy_handler = DummyHandler()
    dummy_engine = TaskEngine(
        handler=dummy_handler,
    )

    dummy_agent = Agent(
        engines=[
            dummy_engine,
        ]
    )

    summary_agent = Agent(
        name="Summary_Synthesizer_Agent",
        goal="Review the metrics from the Addition and Multiplication agents and compile a unified report.",
        role="Lead Synthesizer",
        llm=llm_client,
        prompt_template=prompt_template,
        tool=summary_handler,
        max_retry=1
    )

    # --- DAG Infrastructure & Execution ---
    store = InMemoryStore()
    blueprint = WorkflowBlueprint("Strict Math Aggregator")

    blueprint.add_node(addition_agent, name="Addition_Agent")
    blueprint.add_node(multiplication_agent, name="Multiplication_Agent")
    blueprint.add_node(dummy_agent, name="Summary_Synthesizer_Agent")

    blueprint.add_path(["Addition_Agent", "Multiplication_Agent"], "Summary_Synthesizer_Agent")

    dag_engine = AgentXDag(blueprint=blueprint, store=store, stop_on_node_failure=True)

    initial_input = {"query_instruction": "Please compute operations using the baseline values 12 and 8."}
    await dag_engine.execute(run_id="wf_strict_run_101", initial_ctx=initial_input)

    # Output verification
    checkpoint = store.load("wf_strict_run_101")
    print("\n➕ [Addition Agent]:", dag_engine._extract_output(checkpoint.results.get("Addition_Agent")))
    print("\n✖️ [Multiplication Agent]:", dag_engine._extract_output(checkpoint.results.get("Multiplication_Agent")))
    print("\n📝 [Summary Agent]:\n", dag_engine._extract_output(checkpoint.results.get("Summary_Synthesizer_Agent")))


if __name__ == "__main__":
    asyncio.run(main())