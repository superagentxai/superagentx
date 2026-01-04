import logging

import pytest

from superagentx.agent import Agent
from superagentx.engine import Engine
from superagentx.handler.ai import AIHandler
from superagentx.llm import LLMClient
from superagentx.agentxpipe import AgentXPipe
from superagentx.memory import Memory
from superagentx.prompt import PromptTemplate

logger = logging.getLogger(__name__)

'''
 Run Pytest:  

   1.pytest -s --log-cli-level=INFO tests/pipe/test_ai_pipe.py::TestIOConsolePipe::test_ai_spamfilter
   2.pytest -s --log-cli-level=INFO tests/pipe/test_ai_pipe.py::TestIOConsolePipe::test_writer
   3.pytest -s --log-cli-level=INFO tests/pipe/test_ai_pipe.py::TestIOConsolePipe::test_scorer
'''

discussion = """From: jane@edu.tech.net (Jane Mitchell)
        Subject: Re: <AI and the Future of Learning?>
        Organization: Educational Technologies Inc.
        Lines: 45
        NNTP-Posting-Host: innovate.edu.tech.net

        mark@progress.ai.org (Mark Stevens) writes:
        
        AI tools like ChatGPT and adaptive learning systems are improving education.
        They provide personalized learning experiences and are available 24/7. What’s not to love?
        
        But are we sacrificing meaningful human interaction for efficiency?
        
        I don't think we need to view it as a trade-off. AI isn’t replacing teachers but enhancing their abilities.
        Many educators feel overwhelmed by large class sizes and administrative work—AI can handle repetitive tasks,
        freeing up teachers to focus on students.
        
        But relationships matter. Can an AI ever understand a student’s emotions or struggles the way a human can?
        
        Of course, human relationships are essential. But AI can still assist by identifying students at risk or
        customizing lessons in ways humans can’t efficiently do. For example, AI systems can detect patterns in a
        student’s performance and suggest tailored interventions that might go unnoticed otherwise.
        
        You’re assuming that every student will benefit equally. What about children who need emotional support
        or lack access to technology? Won’t this create a bigger divide?
        
        It’s a valid concern, but that’s not an issue with AI itself. It’s about access. If we address the 
        infrastructure problem—like providing devices and internet to underserved communities—AI can reduce inequalities
        by offering the same level of education to all students, regardless of location.
        
        What if students become dependent on technology and lose critical thinking skills?
        
        That’s a fear I’ve heard before. But it’s no different from when people worried that calculators would ruin math.
        The key lies in how we integrate AI. If teachers emphasize that AI tools are assistants and not replacements for
         thinking, students will still learn how to think critically and creatively.
        
        But what happens when the AI makes mistakes or provides incorrect information? Isn’t there a risk of students
        learning the wrong thing?
        
        Certainly. That’s why teachers remain vital. They must guide students in how to question and cross-check 
        information, even from AI tools. Education has always been about learning to navigate errors, whether from
        a textbook, teacher, or software.
        
        Jane
        """


@pytest.fixture
def ai_client_init() -> dict:
    llm_config = {'model': 'gpt-5-mini', 'llm_type': 'openai', 'async_mode': False}

    # llm_config = {'model': 'anthropic.claude-3-5-sonnet-20240620-v1:0', 'llm_type': 'bedrock', 'async_mode': True}

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
        ),
        'memory': Memory(memory_config={"llm_client": llm_client})
    }
    return response


async def status_callback(event: str, agent_id: str, agent: str, **kwargs):
    logger.info(f"[Callback] Event: {event}")
    logger.info(f"[Callback] Event: {event}, Agent ID: {agent_id}, Agent Name: {agent}  Data: {kwargs}")


class TestIOConsolePipe:

    async def test_ai_spamfilter(self, ai_client_init: dict):
        llm_client: LLMClient = ai_client_init.get('llm')
        prompt_template = ai_client_init.get('prompt_template')
        ai_agent_engine = ai_client_init.get('ai_agent_engine')
        memory = ai_client_init.get('memory')

        spamfilter = Agent(
            name='Spamfilter Agent',
            goal="Analyse the given content and decide whether a text is spam or not.",
            role="spamfilter",
            llm=llm_client,
            prompt_template=prompt_template,
            engines=[ai_agent_engine],
            max_retry=1,

        )

        pipe = AgentXPipe(
            agents=[spamfilter],
            memory=memory,

        )

        _discussion = """
        From: sam@techchange.net (Sam Winters)
        Subject: Re: <Remote Work: A New Era or a Failing Experiment?>
        Organization: TechChange Solutions
        Lines: 47
        NNTP-Posting-Host: hub.techchange.net
        
        david@businesstoday.org (David Carlson) writes:Sam:
        The downside? Reduced productivity, isolation, and a loss of team cohesion. Not to mention, the blurred boundaries between work and personal life are leading to burnout.
        
        David:
        Remote work is the future. It offers flexibility, reduces commute time, and improves work-life balance. Employees are happier, and companies can save on office costs. What’s the downside?
        
        Sam:
        The downside? Reduced productivity, isolation, and a loss of team cohesion. Not to mention, the blurred boundaries between work and personal life are leading to burnout.
        
        David:
        That’s not what most studies show. Surveys indicate that people are more productive at home because they have fewer distractions. Plus, businesses are reporting higher employee satisfaction.
        
        Sam:
        Higher satisfaction? Maybe for now, but let’s wait until the novelty wears off. People need social interaction. Without face-to-face communication, you’ll see a decline in creativity and innovation.
        
        David:
        That’s why tools like Zoom and Slack exist. Teams can stay connected virtually and collaborate without the need to be in the same room.
        
        Sam:
        Virtual meetings are a joke. Half the people don’t pay attention, and the other half multitask. And Slack? It’s just another distraction, with constant notifications breaking everyone’s focus.
        
        Spam Interruption:
        🚨 Looking for the BEST Work-From-Home Setup? 🚨
        🛋️ Get your ergonomic chair and premium desk for only $299! Limited stock! 🤑
        Visit WFHdeals.net NOW to claim yours!
        
        Sam:
        And there it is—more spam. Proof that the remote work trend isn’t all sunshine and rainbows. The internet is filled with distractions. How can anyone work effectively with this nonsense popping up all the time?
        
        David:
        Spam is an issue, but it’s manageable. You can block ads and set notifications to “Do Not Disturb.” The benefits of remote work far outweigh the occasional interruptions.
        
        Sam:
        The benefits? You mean sitting at home, disconnected from colleagues, and pretending to care about work? Remote work is just an excuse for people to slack off. Productivity will tank eventually.
        
        David:
        That’s a bit harsh. Many professionals are thriving in this new environment. It’s about setting boundaries and adapting to change.
        
        Sam:
        We’ll see. I’m betting companies will realize it’s not sustainable. Sooner or later, they’ll start dragging people back to the office when they see the real impact on performance.
        
        David:
        Or they’ll evolve and learn to embrace the new normal. The key is balancing flexibility with accountability.
        
        Sam:
        Balance or not, remote work is a ticking time bomb.
        """
        result = await pipe.flow(
            query_instruction=discussion
        )
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
            engines=[ai_agent_engine],
            max_retry=1,

        )

        scriptwriter = Agent(
            name='Scriptwriter Agent',
            goal="Turn a conversation into a movie script. Only write the dialogue parts. "
                 "Do not start the sentence with an action. Do not specify situational descriptions. Do not write "
                 "parentheticals.",
            role="scriptwriter",
            llm=llm_client,
            prompt_template=prompt_template,
            engines=[ai_agent_engine],
            max_retry=1,
            human_approval=True

        )

        formatter = Agent(
            name='Formatter Agent',
            goal="Format the text as asked. Leave out actions from discussion members that happen between "
                 "brackets, eg (smiling).",
            role="formatter",
            llm=llm_client,
            prompt_template=prompt_template,
            engines=[ai_agent_engine],
            max_retry=1
        )

        pipe = AgentXPipe(
            agents=[analyst, scriptwriter, formatter], stop_if_goal_not_satisfied=False
        )
        result = await pipe.flow(
            query_instruction=discussion,
        )
        logger.info(f"Writer result => \n{result}")
        assert result

    async def test_scorer(self, ai_client_init: dict):
        llm_client: LLMClient = ai_client_init.get('llm')
        prompt_template = ai_client_init.get('prompt_template')
        ai_agent_engine = ai_client_init.get('ai_agent_engine')

        scorer = Agent(
            name='Scorer Agent',
            goal="""
                    This framework provides a structured method to assess the quality of a conversation. 
                    Using a 1-10 scale, the framework highlights strengths and areas for improvement across key 
                    communication factors.
                    Performance Scale:
                    1-3: Poor – The exchange is plagued by major communication problems, leading to misunderstandings.
                    4-6: Average – The dialogue covers some important points but is undermined by noticeable gaps or weaknesses.
                    7-9: Good – The conversation is mostly effective, with only minor issues detracting from the flow.
                    10: Excellent – The dialogue is seamless, fulfilling its intended purpose with precision and clarity.
                    
                    Evaluation Factors:
                    Clarity:
                    Question: Are statements easy to understand, with minimal ambiguity?
                    Importance: Clear communication ensures participants grasp ideas and respond effectively.
                    
                    Relevance:
                    Question: Do the contributions stay aligned with the conversation's topic?
                    Importance: Relevant input keeps the discussion focused and productive.
                    
                    Conciseness:
                    Question: Is the conversation free of unnecessary repetition or irrelevant information?
                    Importance: Brevity makes dialogue efficient without sacrificing meaning.
                    
                    Politeness:
                    Question: Are participants respectful and tactful, even when disagreeing?
                    Importance: Civility fosters constructive dialogue and mutual respect.
                    
                    Engagement:
                    Question: Do participants show interest and actively contribute to the exchange?
                    Importance: Active participation keeps the conversation dynamic and meaningful.
                    
                    Flow:
                    Question: Does the conversation progress smoothly without interruptions or awkward shifts?
                    Importance: A logical flow maintains momentum and coherence in the discussion.
                    
                    Coherence:
                    Question: Do the points fit logically together, building toward a clear outcome?
                    Importance: Coherent exchanges prevent confusion and miscommunication.
                    
                    Responsiveness:
                    Question: Are participants addressing each other’s arguments effectively?
                    Importance: Direct responses promote deeper understanding and resolution of points.
                    
                    Language Use:
                    Question: Is the language appropriate, using correct grammar and vocabulary?
                    Importance: Proper language use ensures professionalism and clarity.
                    
                    Emotional Intelligence:
                    Question: Are participants aware of the emotional undertones in the conversation?
                    Importance: Sensitivity to emotions enhances rapport and prevents unnecessary conflict.
                    """,
            role="scorer",
            llm=llm_client,
            prompt_template=prompt_template,
            engines=[ai_agent_engine]
        )

        pipe = AgentXPipe(
            agents=[scorer]
        )
        result = await pipe.flow(
            query_instruction=discussion,
            verify_goal=False
        )
        logger.info(f"Scorer result => \n{result}")
        assert result
