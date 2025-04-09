import asyncio

from superagentx.agent import Agent
from superagentx.agentxpipe import AgentXPipe
from superagentx.engine import Engine
from superagentx.handler import SerperDevToolHandler
from superagentx.llm import LLMClient
from superagentx.memory import Memory
from superagentx.pipeimpl.iopipe import IOPipe
from superagentx.prompt import PromptTemplate
from superagentx_handlers import ScrapeHandler
from superagentx.handler import AIHandler

output_prompt = """
Change the output format from the context. Give me list of link

Desired Format:
    ["https://www.google.com"],

Don't include any other information.
"""

input_prompt = """
[Content Aggregator Name or Title]
(A tagline that captures the essence of the content you're aggregating)

1. Trending Headlines
Source: Title of the Article
A short description or summary of the article's content.
Why It's Relevant: Brief explanation of why this is noteworthy.

2. Featured Stories
Category: [e.g., Tech, Lifestyle, Entertainment, etc.]
Title: [Story title with link]
Summary: Highlight the most engaging part of the content.
Takeaway/Impact: Key insights for the audience.

3. Must-Reads of the Week
Title: Post, blog, or resource name
Who it's for: Target audience or interest group.
What you'll learn: The primary value offered by the resource.

4. Spotlight Content
Type: [Video, Infographic, Tool, etc.]
Embed or link with a description of its importance.

5. Community Corner (User-generated or audience-submitted content)
Contributor: [Name/Username]
Content Type: [Tweet, Post, Poll, etc.]
Highlight: What makes this content unique.

Ensure to write a BLOG content in this format. DON'T generate json format.
"""


async def get_content_aggregator_pipe():
    llm_config = {
        'model': 'llama3.1',
        'llm_type': 'ollama'
    }
    llm_client = LLMClient(llm_config=llm_config)

    prompt_template = PromptTemplate()

    memory = Memory(
        memory_config={"llm_client": llm_client}
    )

    serper_handler = SerperDevToolHandler()
    crawler_handler = ScrapeHandler()

    serper_prompt = """
    Search web searches based on the user's query.You're provided with a tool that can search the website urls
     'search' and a tool that can retrieves the website urls based on the user query. Total results 1.
    """
    serper_system_prompt = PromptTemplate(
        system_message=serper_prompt
    )

    crawler_prompt = """
    Extract the content from the provided context. You're provided with a tool that can get the content 'scrap_content'
     and a tool that can retrieves the content from the given output context.
    """
    crawler_system_prompt = PromptTemplate(
        system_message=crawler_prompt
    )

    serper_engine = Engine(
        handler=serper_handler,
        llm=llm_client,
        prompt_template=serper_system_prompt
    )

    crawler_engine = Engine(
        handler=crawler_handler,
        llm=llm_client,
        prompt_template=crawler_system_prompt
    )

    serper_agent = Agent(
        name="Serper Agent",
        role=f'You are the website link provider and generate the following format',
        goal=f'Generate the list of website urls in the list format\n Format:\n{output_prompt}',
        llm=llm_client,
        prompt_template=serper_system_prompt,
        engines=[serper_engine],
        output_format=output_prompt,
        max_retry=1
    )

    crawler_agent = Agent(
        name="crawler Agent",
        goal=f"Provide a blog with briefly",
        role=f"You are a Blog writer. Generate the content briefly with minimum 5 paragraphs based"
             f" on the given context.",
        llm=llm_client,
        prompt_template=crawler_system_prompt,
        engines=[crawler_engine],
        max_retry=2
    )

    pipe = AgentXPipe(
        agents=[
            serper_agent,
            crawler_agent,
        ],
        # memory=memory
    )
    return pipe


async def main():
    pipe = await get_content_aggregator_pipe()

    # Create IO Cli Console - Interface
    io_pipe = IOPipe(
        search_name='SuperAgentX Trip Planner',
        agentx_pipe=pipe,
        read_prompt=f"\n[bold green]Enter your search here"
    )
    await io_pipe.start()

if __name__ == "__main__":
    asyncio.run(main())
