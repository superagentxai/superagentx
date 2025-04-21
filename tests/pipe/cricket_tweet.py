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

    browser_engine = BrowserEngine(
        llm=llm_client,
        prompt_template=prompt_template,
        browser_instance_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    )

    cricket_analyse_agent = Agent(
        goal="Complete the user's input.",
        role="You are the cricket analyser",
        llm=llm_client,
        prompt_template=prompt_template,
        max_retry=1,
        engines=[browser_engine]
    )

    # twitter_agent = Agent(
    #     goal='Summarize and post the content in x.com',
    #     role="Twitter Agent",
    #     llm=llm_client,
    #     prompt_template=prompt_template,
    #     max_retry=1,
    #     engines=[browser_engine]
    # )

    # Pipe Interface to send it to public accessible interface (Cli Console / WebSocket / Restful API)
    pipe = AgentXPipe(
        agents=[cricket_analyse_agent],

    )
    return pipe
