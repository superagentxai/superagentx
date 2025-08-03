import asyncio

from superagentx.agent import Agent
from superagentx.browser_engine import BrowserEngine
from superagentx.llm import LLMClient
from superagentx.prompt import PromptTemplate


async def main():
    llm_client: LLMClient = LLMClient(llm_config={'model': 'gpt-4.1', 'llm_type': 'openai'})

    prompt_template = PromptTemplate()

    browser_engine = BrowserEngine(
        llm=llm_client,
        prompt_template=prompt_template,

    )
    ENTRA_STEPS = """
    Go to the login page: https://entra.microsoft.com
From the left sidebar, select Entra ID.
On the Entra ID overview page, navigate to the Protection menu.
Under the Protection menu, select Conditional Access.
Select a relevant policy from the list that is configured to manage user session controls.
Under the Access controls section of the policy, click on the Session control link.
Display the configuration page for session controls. This page shows the settings for 'Sign-in frequency' and 'Persistent browser session', which provide evidence of session termination policies.


    """
    query_instruction = ENTRA_STEPS

    fifo_analyser_agent = Agent(
        goal="Complete user's task.",
        role="You are an Automation Agent",
        llm=llm_client,
        prompt_template=prompt_template,
        max_retry=1,
        engines=[browser_engine]
    )

    result = await fifo_analyser_agent.execute(
        query_instruction=query_instruction
    )

    print(result)


asyncio.run(main())
