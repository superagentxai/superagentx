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
    print("Travel planner")

    '''
            Level 1
        ────────────────────────────────
        
        Travel_Planner_Agent
                  │
                  ▼
        
        Level 2
        ────────────────────────────────
        
        Flight_Planner_Agent     Hotel_Planner_Agent
                  │                      │
        
                  ▼                      ▼
        
        Level 3
        ────────────────────────────────
        
        Visa_Agent          Local_Tour_Agent
                  │               │
        
                  └──────┬────────┘
        
                         ▼
        
        Level 4
        ────────────────────────────────
        
        Itinerary_Agent
    '''

    # 1. Initialize LLM Client
    llm_client = LLMClient(
        llm_config={
            "model": "gemini/gemini-2.5-flash"
        }
    )

    handler = AIHandler(llm=llm_client)

    travel_agent = Agent(
        name="Travel_Planner_Agent",
        role="Travel Consultant",
        goal="Understand travel request and prepare travel planning instructions",
        tool=handler,
        llm=llm_client,
        prompt_template=PromptTemplate(
            system_message="""
    You are a travel planner.

    Read the user's request.

    Extract:
    - destination
    - duration
    - travellers
    - budget
    - travel style

    Return planning instructions.
    """
        )
    )

    flight_agent = Agent(
        name="Flight_Planner_Agent",
        role="Flight Specialist",
        goal="Recommend suitable flights",
        tool=handler,
        llm=llm_client,
        prompt_template=PromptTemplate(
            system_message="""
    Recommend outbound and return flights.

    Include:

    - airlines
    - estimated price
    - travel duration
    """
        )
    )

    hotel_agent = Agent(
        name="Hotel_Planner_Agent",
        role="Hotel Specialist",
        goal="Recommend hotels",
        tool=handler,
        llm=llm_client,
        prompt_template=PromptTemplate(
            system_message="""
    Recommend hotels.

    Include:

    - area
    - hotel
    - approximate price
    - reason
    """
        )
    )

    visa_agent = Agent(
        name="Visa_Agent",
        role="Visa Consultant",
        goal="Explain visa requirements",
        tool=handler,
        llm=llm_client,
        prompt_template=PromptTemplate(
            system_message="""
    Based on destination,

    Explain:

    - visa needed
    - documents
    - processing time
    """
        )
    )

    tour_agent = Agent(
        name="Local_Tour_Agent",
        role="Tour Guide",
        goal="Recommend attractions",
        tool=handler,
        llm=llm_client,
        prompt_template=PromptTemplate(
            system_message="""
    Suggest attractions.

    Organize by day.

    Recommend local transport.
    """
        )
    )

    itinerary_agent = Agent(
        name="Itinerary_Agent",
        role="Travel Coordinator",
        goal="Create final itinerary",
        tool=handler,
        llm=llm_client,
        prompt_template=PromptTemplate(
            system_message="""
    Combine all previous outputs.

    Produce

    Day 1
    Day 2
    Day 3
    ...

    Include

    Flights
    Hotels
    Visa
    Places
    Budget Summary
    Travel Tips
    """
        )
    )

    blueprint = WorkflowBlueprint(name="Travel_Planner")

    blueprint.add_node(travel_agent)
    blueprint.add_node(flight_agent)
    blueprint.add_node(hotel_agent)
    blueprint.add_node(visa_agent)
    blueprint.add_node(tour_agent)
    blueprint.add_node(itinerary_agent)

    travel_planning_group = [
        "Flight_Planner_Agent",
        "Hotel_Planner_Agent"
    ]

    blueprint.add_path(
        "Travel_Planner_Agent",
        travel_planning_group
    )

    blueprint.add_path(
        "Flight_Planner_Agent",
        "Visa_Agent"
    )

    blueprint.add_path(
        "Hotel_Planner_Agent",
        "Local_Tour_Agent"
    )

    travel_summary_group = [
        "Visa_Agent",
        "Local_Tour_Agent"
    ]

    blueprint.add_path(
        travel_summary_group,
        "Itinerary_Agent"
    )

    run_id = "travel_demo"

    store = InMemoryStore()

    dag_engine = AgentXDag(
        blueprint=blueprint,
        store=store,
        stop_if_goal_not_satisfied=False,
        workflow_store=True
    )

    await dag_engine.execute(
        run_id=run_id,
        initial_ctx={
            "query_instruction":
                "Plan a 5-day family vacation to Singapore from Chennai with a budget of $3000.",
            "pre_result": []
        }
    )

if __name__ == "__main__":
    asyncio.run(main())