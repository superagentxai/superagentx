import asyncio
import logging

from superagentx.agent import Agent
from superagentx.handler.ai import AIHandler
from superagentx.llm import LLMClient
from superagentx.prompt import PromptTemplate

# Import your newly designed stateful DAG orchestrator classes
# (Make sure AgentXDag includes the string serialization context fix for multiple parents)
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
    print("Simple Hierarchy")

    # 1. Initialize LLM Client
    llm_client = LLMClient(
        llm_config={
            "model": "gemini/gemini-2.5-flash"
        }
    )

    handler = AIHandler(llm=llm_client)

    root_agent = Agent(
        name="Root_Agent",
        role="Workflow Manager",
        goal="Understand the request and delegate work",
        tool=handler,
        llm=llm_client,
        prompt_template=PromptTemplate(
            system_message="""
    Read the user's request.

    Return one short sentence describing the task.

    Maximum 5 words.
    """
        )
    )

    a1_agent = Agent(
        name="A1_Agent",
        role="Left Worker",
        goal="Generate left branch result",
        tool=handler,
        llm=llm_client,
        prompt_template=PromptTemplate(
            system_message="""
    Read previous output.

    Reply with:

    Left branch completed.

    Nothing else.
    """
        )
    )

    a2_agent = Agent(
        name="A2_Agent",
        role="Right Worker",
        goal="Generate right branch result",
        tool=handler,
        llm=llm_client,
        prompt_template=PromptTemplate(
            system_message="""
    Read previous output.

    Reply with:

    Right branch completed.

    Nothing else.
    """
        )
    )

    b1_agent = Agent(
        name="B1_Agent",
        role="Left Refiner",
        goal="Refine left branch",
        tool=handler,
        llm=llm_client,
        prompt_template=PromptTemplate(
            system_message="""
    Read previous output.

    Reply with:

    Left refined.

    Nothing else.
    """
        )
    )

    b2_agent = Agent(
        name="B2_Agent",
        role="Right Refiner",
        goal="Refine right branch",
        tool=handler,
        llm=llm_client,
        prompt_template=PromptTemplate(
            system_message="""
    Read previous output.

    Reply with:

    Right refined.

    Nothing else.
    """
        )
    )

    final_agent = Agent(
        name="Final_Agent",
        role="Aggregator",
        goal="Merge all branch outputs",
        tool=handler,
        llm=llm_client,
        prompt_template=PromptTemplate(
            system_message="""
    Combine all previous agent outputs.

    Return a short summary in one sentence.

    Maximum 10 words.
    """
        )
    )

    blueprint = WorkflowBlueprint(name="Simple_Hierarchy")

    blueprint.add_node(root_agent)
    blueprint.add_node(a1_agent)
    blueprint.add_node(a2_agent)
    blueprint.add_node(b1_agent)
    blueprint.add_node(b2_agent)
    blueprint.add_node(final_agent)

    # Level 1
    blueprint.add_path(
        "Root_Agent",
        ["A1_Agent", "A2_Agent"]
    )

    # Level 2
    blueprint.add_path("A1_Agent", "B1_Agent")
    blueprint.add_path("A2_Agent", "B2_Agent")

    # Level 3 (Merge)
    blueprint.add_path(
        ["B1_Agent", "B2_Agent"],
        "Final_Agent"
    )

    store = InMemoryStore()

    dag_engine = AgentXDag(
        blueprint=blueprint,
        store=store,
        stop_if_goal_not_satisfied=False,
        workflow_store=True
    )

    await dag_engine.execute(
        run_id="hierarchy_test",
        initial_ctx={
            "query_instruction": "Test hierarchy",
            "pre_result": []
        }
    )

if __name__ == "__main__":
    asyncio.run(main())



