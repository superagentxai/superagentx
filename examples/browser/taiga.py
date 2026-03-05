import asyncio

from superagentx.agent import Agent
from superagentx.agentxpipe import AgentXPipe
from superagentx.browser_engine import BrowserEngine
from superagentx.llm import LLMClient
from superagentx.prompt import PromptTemplate


async def main():
    llm_config = {'model': 'openai/gpt-5-mini'}

    llm_client: LLMClient = LLMClient(llm_config=llm_config)

    prompt_template = PromptTemplate()

    browser_engine = BrowserEngine(
        llm=llm_client,
        prompt_template=prompt_template,

    )

    TAIGA_STEPS = """
    Setting Up Top-Page Attributes for Your Taiga Project's Status Page

    Here's how to choose which project attributes appear prominently on your Taiga project's public status page:

    1. Open Taiga and Log In: First, open your web browser and go to your Taiga instance URL (for example, https://tree.taiga.io/). Then, sign in to your Taiga account.
    2. Remove Cookie Warning: If a cookie warning element appears in the DOM, remove it before proceeding.
    3. Choose a Project: From your Taiga dashboard or main project list, click on any visible project to enter it. DO NOT USE any dropdown menus to select the project.
    4. Access Project Settings: Once you're inside the project, find the left-hand sidebar. In that sidebar, click on "Settings."
    5. On the left side menu, Click 'ATTRIBUTES' and goto to its second level sub-menu called 'STATUSES'. Once you successfully navigated to "STATUSES" menu, job completed.

    ### Important Notes:

    * **One Attempt Only**: This is a **single-try operation**. If any step after you've successfully logged in fails for your chosen vendor (e.g., the "Reviews" icon isn't there, reviews don't load, or an error occurs during extraction), **do not try again**.
    * **Read-Only Task**: Your job is solely to **collect data**. Do not perform any edits or deletions.
    * **Failure Handling**: If an action cannot be completed, it will be retried once. If the second attempt also fails, immediately report the following error: "**Failed to collect evidence for the selected vendor. Recommend using the EVC API for more reliable data extraction.**"
        * **Note**: If there's **no review data available** for a vendor after clicking the icon, this **should not be considered a failure**.
    """

    analyser_agent = Agent(
        goal="Complete user's task.",
        role="You are an EVC GRC Evidence Collector",
        llm=llm_client,
        prompt_template=prompt_template,
        max_retry=1,
        engines=[browser_engine]
    )

    pipe = AgentXPipe(
        agents=[analyser_agent],
        workflow_store=True
    )

    result = await pipe.flow(
        query_instruction=TAIGA_STEPS
    )

    print(result)


asyncio.run(main())
