import pytest

from agentx.agent.agent import Agent
from agentx.agent.engine import Engine
from agentx.handler.ai_handler import AIHandler
from agentx.io import IOConsole
from agentx.llm import LLMClient
from agentx.pipe import AgentXPipe
from agentx.prompt import PromptTemplate


'''
 Run Pytest:  

   1. pytest -s --log-cli-level=INFO tests/pipe/test_ai_pipe.py::TestIOConsolePipe::test_ai_pipe
'''

@pytest.fixture
def ai_client_init() -> dict:
    llm_config = {'model': 'gpt-4-turbo-2024-04-09', 'llm_type': 'openai'}

    llm_client: LLMClient = LLMClient(llm_config=llm_config)
    response = {'llm': llm_client, 'llm_type': 'openai'}
    return response

class TestIOConsolePipe:

    async def test_ai_pipe(self, ai_client_init: dict):
        llm_client: LLMClient = ai_client_init.get('llm')
        content_handler = AIHandler(llm=llm_client)
        prompt_template = PromptTemplate()
        ai_agent_engine = Engine(
            handler=content_handler,
            prompt_template=prompt_template,
            llm=llm_client
        )

        spamfilter = Agent(
            name='Spamfilter Agent',
            goal="Decide whether a text is spam or not.",
            role="spamfilter",
            llm=llm_client,
            prompt_template=prompt_template,
            engines=[ai_agent_engine]
        )

        analyst = Agent(
            name='Analyst Agent',
            goal="You will distill all arguments from all discussion members. Identify who said what."
                 "You can reword what they said as long as the main discussion points remain.",
            role="analyse",
            llm=llm_client,
            prompt_template=prompt_template,
            engines=[ai_agent_engine]
        )

        scriptwriter = Agent(
            name='Scriptwriter Agent',
            goal="Turn a conversation into a movie script. Only write the dialogue parts. "
                 "Do not start the sentence with an action. Do not specify situational descriptions. Do not write parentheticals.",
            role="scriptwriter",
            llm=llm_client,
            prompt_template=prompt_template,
            engines=[ai_agent_engine]

        )

        formatter = Agent(
            name='Formatter Agent',
            goal="Format the text as asked. Leave out actions from discussion members that happen between "
                 "brackets, eg (smiling).",
            role="formatter",
            llm=llm_client,
            prompt_template=prompt_template,
            engines=[ai_agent_engine]

        )

        scorer = Agent(
            name='Scorer Agent',
            goal="""
             You score a dialogue assessing various aspects of the exchange between the participants using a 1-10 scale, where 1 is the lowest performance and 10 is the highest:
            Scale:
            1-3: Poor - The dialogue has significant issues that prevent effective communication.
            4-6: Average - The dialogue has some good points but also has notable weaknesses.
            7-9: Good - The dialogue is mostly effective with minor issues.
            10: Excellent - The dialogue is exemplary in achieving its purpose with no apparent issues.
            Factors to Consider:
            Clarity: How clear is the exchange? Are the statements and responses easy to understand?
            Relevance: Do the responses stay on topic and contribute to the conversation's purpose?
            Conciseness: Is the dialogue free of unnecessary information or redundancy?
            Politeness: Are the participants respectful and considerate in their interaction?
            Engagement: Do the participants seem interested and actively involved in the dialogue?
            Flow: Is there a natural progression of ideas and responses? Are there awkward pauses or interruptions?
            Coherence: Does the dialogue make logical sense as a whole?
            Responsiveness: Do the participants address each other's points adequately?
            Language Use: Is the grammar, vocabulary, and syntax appropriate for the context of the dialogue?
            Emotional Intelligence: Are the participants aware of and sensitive to the emotional tone of the dialogue?
            """,
            role="scorer",
            llm=llm_client,
            prompt_template=prompt_template,
            engines=[ai_agent_engine]

        )
        pipe = AgentXPipe(
            io=IOConsole(
                read_phrase="\n\n\nEnter your query here:\n\n=>",
                write_phrase="\n\n\nYour result is =>\n\n"
            ),
            agents=[analyst, scriptwriter, formatter]
        )
        await pipe.flow()
