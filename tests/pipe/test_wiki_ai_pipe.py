import logging

import pytest

from superagentx.agent.agent import Agent
from superagentx.agent.engine import Engine
from superagentx.handler.ai import AIHandler
from superagentx.handler.wikipedia import WikipediaHandler
from superagentx.llm import LLMClient
from superagentx.agentxpipe import AgentXPipe
from superagentx.prompt import PromptTemplate

logger = logging.getLogger(__name__)


class TestWikiAIPipe:

    async def test_wiki_ai_sequence_pipe(self):
        # llm_config = {'model': 'gpt-4o', 'llm_type': 'openai'}
        # llm_config = {'model': 'anthropic.claude-3-5-sonnet-20240620-v1:0', 'llm_type': 'bedrock', 'async_mode': True}
        # llm_config = {'model': 'anthropic.claude-3-5-sonnet-20240620-v1:0', 'llm_type': 'bedrock'}
        llm_config = {'model': 'mistral.mistral-large-2402-v1:0', 'llm_type': 'bedrock', 'async_mode': True}
        llm_client: LLMClient = LLMClient(llm_config=llm_config)
        content_handler = AIHandler(llm=llm_client)
        prompt_template = PromptTemplate()

        wikipedia_handler = WikipediaHandler()

        wikipedia_engine = Engine(handler=wikipedia_handler, prompt_template=prompt_template, llm=llm_client)

        wiki_agent = Agent(
            name='Content Retriever Agent',
            goal='Get the summary from the wikipedia for the given query and validate',
            role="Content Retriever",
            llm=llm_client,
            prompt_template=prompt_template,
            engines=[wikipedia_engine],
            max_retry=1
        )

        ai_agent_engine = Engine(
            handler=content_handler,
            prompt_template=prompt_template,
            llm=llm_client
        )

        goal = """ Write as biography story about the person from the given content. """
        biographer_agent = Agent(
            name='Biography Agent',
            goal=goal,
            role="Biographer",
            llm=llm_client,
            prompt_template=prompt_template,
            engines=[ai_agent_engine],
            max_retry=3
        )

        pipe = AgentXPipe(
            agents=[wiki_agent, biographer_agent]
        )

        result = await pipe.flow(query_instruction="Walt Disney")

        logger.info(f"Biographer result => \n{result}")
