import logging

import pytest

from agentx.agent.agent import Agent
from agentx.agent.engine import Engine
from agentx.handler.ai_handler import AIHandler
from agentx.llm import LLMClient
from agentx.pipe import AgentXPipe
from agentx.prompt import PromptTemplate

logger = logging.getLogger(__name__)

'''
 Run Pytest:  

   1.pytest -s --log-cli-level=INFO tests/pipe/test_ai_pipe.py::TestIOConsolePipe::test_ai_spamfilter
   2.pytest -s --log-cli-level=INFO tests/pipe/test_ai_pipe.py::TestIOConsolePipe::test_writer
   3.pytest -s --log-cli-level=INFO tests/pipe/test_ai_pipe.py::TestIOConsolePipe::test_scorer
'''

discussion = """From: keith@cco.caltech.edu (Keith Allan Schneider)
        Subject: Re: <Political Atheists?
        Organization: California Institute of Technology, Pasadena
        Lines: 50
        NNTP-Posting-Host: punisher.caltech.edu

        bobbe@vice.ICO.TEK.COM (Robert Beauchaine) writes:

        >>I think that about 70% (or so) people approve of the
        >>death penalty, even realizing all of its shortcomings.  Doesn't this make
        >>it reasonable?  Or are *you* the sole judge of reasonability?
        >Aside from revenge, what merits do you find in capital punishment?

        Are we talking about me, or the majority of the people that support it?
        Anyway, I think that "revenge" or "fairness" is why most people are in
        favor of the punishment.  If a murderer is going to be punished, people
        that think that he should "get what he deserves."  Most people wouldn't
        think it would be fair for the murderer to live, while his victim died.

        >Revenge?  Petty and pathetic.

        Perhaps you think that it is petty and pathetic, but your views are in the
        minority.

        >We have a local televised hot topic talk show that very recently
        >did a segment on capital punishment.  Each and every advocate of
        >the use of this portion of our system of "jurisprudence" cited the
        >main reason for supporting it:  "That bastard deserved it".  True
        >human compassion, forgiveness, and sympathy.

        Where are we required to have compassion, forgiveness, and sympathy?  If
        someone wrongs me, I will take great lengths to make sure that his advantage
        is removed, or a similar situation is forced upon him.  If someone kills
        another, then we can apply the golden rule and kill this person in turn.
        Is not our entire moral system based on such a concept?

        Or, are you stating that human life is sacred, somehow, and that it should
        never be violated?  This would sound like some sort of religious view.

        >>I mean, how reasonable is imprisonment, really, when you think about it?
        >>Sure, the person could be released if found innocent, but you still
        >>can't undo the imiprisonment that was served.  Perhaps we shouldn't
        >>imprision people if we could watch them closely instead.  The cost would
        >>probably be similar, especially if we just implanted some sort of
        >>electronic device.
        >Would you rather be alive in prison or dead in the chair?  

        Once a criminal has committed a murder, his desires are irrelevant.

        And, you still have not answered my question.  If you are concerned about
        the death penalty due to the possibility of the execution of an innocent,
        then why isn't this same concern shared with imprisonment.  Shouldn't we,
        by your logic, administer as minimum as punishment as possible, to avoid
        violating the liberty or happiness of an innocent person?

        keith
        """

@pytest.fixture
def ai_client_init() -> dict:
    llm_config = {'model': 'gpt-4-turbo-2024-04-09', 'llm_type': 'openai'}

    llm_client: LLMClient = LLMClient(llm_config=llm_config)
    content_handler = AIHandler(llm=llm_client)
    prompt_template = PromptTemplate()
    response = {
        'llm': llm_client,
        'llm_type': 'openai',
        'content_handler': content_handler,
        'prompt_template': prompt_template,
        'ai_agent_engine': Engine(
            handler=content_handler,
            prompt_template=prompt_template,
            llm=llm_client
        )
    }
    return response

class TestIOConsolePipe:

    async def test_ai_spamfilter(self, ai_client_init: dict):
        llm_client: LLMClient = ai_client_init.get('llm')
        prompt_template = ai_client_init.get('prompt_template')
        ai_agent_engine = ai_client_init.get('ai_agent_engine')

        spamfilter = Agent(
            name='Spamfilter Agent',
            goal="Decide whether a text is spam or not.",
            role="spamfilter",
            llm=llm_client,
            prompt_template=prompt_template,
            engines=[ai_agent_engine]
        )

        pipe = AgentXPipe(
            agents=[spamfilter]
        )
        result = await pipe.flow(query_instruction=discussion)
        logger.info(f"Spamfilter result => \n{result}")
        assert result

    async def test_writer(self, ai_client_init: dict):
        llm_client: LLMClient = ai_client_init.get('llm')
        prompt_template = ai_client_init.get('prompt_template')
        ai_agent_engine = ai_client_init.get('ai_agent_engine')

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

        pipe = AgentXPipe(
            agents=[analyst, scriptwriter, formatter]
        )
        assert await pipe.flow(query_instruction=discussion)

    async def test_scorer(self, ai_client_init: dict):
        llm_client: LLMClient = ai_client_init.get('llm')
        prompt_template = ai_client_init.get('prompt_template')
        ai_agent_engine = ai_client_init.get('ai_agent_engine')

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
            agents=[scorer]
        )
        assert await pipe.flow(query_instruction=discussion)