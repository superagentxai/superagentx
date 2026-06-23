import asyncio

from superagentx.agent import Agent
from superagentx.agentxpipe import AgentXPipe
from superagentx.handler.ai import AIHandler
from superagentx.handler.task.greetings.welcome_handler import WelcomeHandler
from superagentx.llm import LLMClient
from superagentx.prompt import PromptTemplate
from superagentx.task_engine import TaskEngine


async def main():

    llm_client = LLMClient(
        llm_config={
            "model": "gemini/gemini-2.5-flash"
        }
    )

    ai_handler = AIHandler(llm=llm_client)

    # ----------------------------------
    # AI Agent
    # ----------------------------------
    gold_rate_agent = Agent(
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
        human_approval=False
    )

    handler = WelcomeHandler(first_name="John", last_name="Doe")

    engine = TaskEngine(
        handler=handler,
        instructions=[
            {"send_greeting": {"message": "$prev_result"}}
        ]
    )

    task_agent = Agent(
        engines=[engine]
    )

    # ----------------------------------
    # Agent Pipeline
    # ----------------------------------
    pipe = AgentXPipe(
        agents=[
            gold_rate_agent,
            task_agent
        ],
        workflow_store=True
    )

    result = await pipe.flow(
        query_instruction="Generate today's gold rates in JSON."
    )

    print(result)


if __name__ == "__main__":
    asyncio.run(main())