import asyncio
import uuid
from rich import print as rprint
from superagentx.agent import Agent
from superagentx.agentxpipe import AgentXPipe
from superagentx.engine import Engine
from superagentx.llm import LLMClient
from superagentx.memory import Memory
from superagentx.prompt import PromptTemplate
from superagentx.handler import AIHandler

async def get_test_ai_handler_pipe() -> AgentXPipe:
    # LLM Configuration
    llm_config = {
        'llm_type': 'openai'
    }
    llm_client = LLMClient(llm_config=llm_config)

    # Enable Memory
    memory = Memory(memory_config={"llm_client": llm_client})

    ai_handler = AIHandler(
        llm=llm_client
    )

    # Prompt Template
    prompt_template = PromptTemplate()

    # Create Engine
    ai_engine = Engine(
        handler=ai_handler,
        llm=llm_client,
        prompt_template=prompt_template
    )

    # Create Agents
    ai_agent = Agent(
        name='AI agent',
        goal="Get me the best results",
        role="You are the best at answering",
        llm=llm_client,
        prompt_template=prompt_template,
        engines=[ai_engine]
    )

    # Expose via pipe for interaction
    pipe = AgentXPipe(
        agents=[ai_agent],
        memory=memory
    )

    return pipe


conversation_id = uuid.uuid4().hex  # Unique ID for tracking this conversation

async def main():

    conversation_pipe = await get_test_ai_handler_pipe()

    while True:
        user_input = input(f"Enter Your Query Here: ")
        result = await conversation_pipe.flow(
            query_instruction=user_input,
            conversation_id=conversation_id  # Context maintained here
        )
        print(result)


if __name__ == "__main__":
    asyncio.run(main())