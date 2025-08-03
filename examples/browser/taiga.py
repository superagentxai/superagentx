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
    TAIGA_STEPS = """
    Setting Up Top-Page Attributes for Your Taiga Project's Status Page

    Here's how to choose which project attributes appear prominently on your Taiga project's public status page:

    1. Open Taiga and Log In: First, open your web browser and go to your Taiga instance URL (for example, https://tree.taiga.io/). Then, sign in to your Taiga account.
    2. Select Your Project: Look for the "Projects" dropdown usually located at the top left of the screen. Click it, and then choose the specific project in the dropdown and copy the selected project the URL.
    3. Access Project Settings: From copied URL get the URL like https:// tree.taiga.io/<<project>> and append this path after you modified '/admin/project-profile/details' and hit the URL.
    4. Go to Attributes: Within the project settings, navigate to and click on "Attributes." From here, you'll be able to manage and select which attributes are displayed on your project's status page.

    ### Important Notes:

    * **One Attempt Only**: This is a **single-try operation**. If any step after you've successfully logged in fails for your chosen vendor (e.g., the "Reviews" icon isn't there, reviews don't load, or an error occurs during extraction), **do not try again**.
    * **Read-Only Task**: Your job is solely to **collect data**. Do not perform any edits or deletions.
    * **Failure Handling**: If any action fails (e.g., you can't click the "Reviews" icon or extract data), immediately report: "**Failed to collect evidence for the selected vendor. Recommend using the EVC API for more reliable data extraction.**"
        * **Note**: If there's **no review data available** for a vendor after clicking the icon, this **should not be considered a failure**.
    """
    query_instruction = TAIGA_STEPS

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
