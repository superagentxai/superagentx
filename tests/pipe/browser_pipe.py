from superagentx.llm import LLMClient
from superagentx.browser_engine import BrowserEngine
from superagentx.engine import Engine
from superagentx.agent import Agent
from superagentx.prompt import PromptTemplate
from superagentx.handler.ai import AIHandler
from superagentx.agentxpipe import AgentXPipe
import logging

logger = logging.getLogger(__name__)


async def get_browser_pipe() -> AgentXPipe:
    llm_config = {'model': 'gpt-4o', 'llm_type': 'openai'}
    llm_client: LLMClient = LLMClient(llm_config=llm_config)

    prompt_template = PromptTemplate()

    content_creator_handler = AIHandler(
        llm=llm_client,
        role="You're a Technology blog expert",
        story_content="Create twitter content about Agent AI"
    )

    content_creator_engine = Engine(
        handler=content_creator_handler,
        llm=llm_client,
        prompt_template=prompt_template
    )

    content_creator_agent = Agent(
        name="Content Tweet Agent",
        role='Technology Expert',
        goal='Generate content',
        llm=llm_client,
        prompt_template=prompt_template,
        engines=[content_creator_engine]
    )

    browser_engine = BrowserEngine(
        llm=llm_client,
        prompt_template=prompt_template,
        # browser_instance_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    )

    goal = """Analyse user input and get details from browser and construct responses."""

    browser_agent = Agent(
        goal=goal,
        role="You are a Browser Agent AI Assistant",
        llm=llm_client,
        prompt_template=prompt_template,
        max_retry=1,
        engines=[browser_engine]
    )

    # Pipe Interface to send it to public accessible interface (Cli Console / WebSocket / Restful API)
    pipe = AgentXPipe(
        agents=[content_creator_agent, browser_agent],

    )
    return pipe
