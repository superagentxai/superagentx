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
    print("🚀 Testing Parallel Agents in SuperAgentX (DAG Architecture)")

    # Initialize LLM & Handler
    llm_config = {"model": "gemini/gemini-2.5-flash"}
    llm_client = LLMClient(llm_config=llm_config)

    llm_config = {"model": "gemini/gemini-2.5-flash", 'llm_type': "litellm"}
    llm_client = LLMClient(llm_config=llm_config)

    # Step 2: Setup MCP tool handler (Reddit trending analyzer)
    # Note: You need to install the mcp-server-reddit package before running this step.

    content_creator_handler = AIHandler(llm=llm_client)

    # Step 3: Create Prompt Template
    prompt_template = PromptTemplate()


    # Step 5: Define Reddit Agent
    agent = Agent(
                  name="Reddit_Trend_Generator",
                  goal="Generate content based on social media posts user input",
                  role="You're Content Generator",
                  llm=llm_client, prompt_template=prompt_template,
                  tool=content_creator_handler,
                  max_retry=1)

    store = InMemoryStore()
    blueprint = WorkflowBlueprint("Content Generator Blueprint")

    # Register the agent. Since there are no dependencies, we don't call blueprint.add_path()
    blueprint.add_node(agent, name="Reddit_Trend_Generator")

    # 4. Instantiate the orchestration engine
    dag_engine = AgentXDag(
        blueprint=blueprint,
        store=store,
        stop_on_node_failure=True
    )

    run_id = "wf_run_single_agent_101"
    initial_input = {"query_instruction": "Analyze top rust-lang web frameworks on Reddit"}

    # 5. Execute the DAG
    final_states = await dag_engine.execute(run_id=run_id, initial_ctx=initial_input)
    print(f"Final states: {final_states}")
    print(f"🎉 Agent Execution Status: {final_states.get('Reddit_Trend_Generator')}")
    for node_name, state in final_states.items():
        print(f"Node Node Name: [{node_name:<25}] -> Lifecycle State: {state.value} ")
        print(f"Node Node {type(state)}")


if __name__ == "__main__":
    asyncio.run(main())