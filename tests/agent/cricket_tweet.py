import asyncio
from rich import print as rprint
from superagentx.agent import Agent
from superagentx.browser_engine import BrowserEngine

from superagentx.llm import LLMClient
from superagentx.prompt import PromptTemplate
import warnings
import logging

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)

async def main():
    # llm_config = {'model': 'gpt-4o', 'llm_type': 'openai'}
    llm_config = {'llm_type': 'gemini', 'model': 'gemini-2.0-flash'}
    llm_client: LLMClient = LLMClient(llm_config=llm_config)

    prompt_template = PromptTemplate()

    browser_engine = BrowserEngine(
        llm=llm_client,
        prompt_template=prompt_template,
        # browser_instance_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    )
    query_instruction = input("\n Enter your task: ")
    logger.info(f"Query Input : {query_instruction}")
    task = f""" 
            1. Analyse and find the result for the given {query_instruction}.
            2. Goto https://x.com/compose/post and click and set focus.
            3. Write the a detail result using input_text.
            3. Review the tweet before post it for submit.
            4. Find 'Post' and Click the 'Post' the button to tweet the result!
            
            Important:
            1. DO NOT write the post as reply
            2. DO NOT post more than one.

        """

    cricket_analyse_agent = Agent(
        goal="Complete user's task.",
        role="You are a Cricket Expert Reviewer",
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
