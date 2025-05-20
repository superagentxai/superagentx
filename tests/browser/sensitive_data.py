import asyncio
import logging

from rich import print as rprint
from superagentx.agent import Agent
from superagentx.browser_engine import BrowserEngine

from superagentx.llm import LLMClient
from superagentx.prompt import PromptTemplate
import warnings

warnings.filterwarnings('ignore')

sh = logging.StreamHandler()
logging.basicConfig(
    level="INFO",
    format='%(asctime)s -%(levelname)s - %(name)s - %(funcName)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[sh]
)


async def main():
    llm_config = {'model': 'gpt-4o', 'llm_type': 'openai', 'async_mode': True}

    llm_client: LLMClient = LLMClient(llm_config=llm_config)

    prompt_template = PromptTemplate()
    sensitive_data = {'x_name': '<email-id>', 'x_password': '<password>'}

    browser_engine = BrowserEngine(
        llm=llm_client,
        prompt_template=prompt_template,
        sensitive_data=sensitive_data
    )
    task = 'go to gmail and login with x_name and x_password'

    cricket_analyse_agent = Agent(
        goal="Complete user's task.",
        role="You are a Gmail Expert",
        llm=llm_client,
        prompt_template=prompt_template,
        max_retry=1,
        engines=[browser_engine]
    )

    result = await cricket_analyse_agent.execute(
        query_instruction=task
    )
    rprint(result)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, asyncio.CancelledError):
        rprint("\nUser canceled the [bold yellow][i]pipe[/i]!")