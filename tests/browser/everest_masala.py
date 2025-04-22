import os
import warnings

from superagentx.handler.base import BaseHandler
from superagentx.handler.decorators import tool

with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=UserWarning)

import logging
import pytest
from superagentx.agent import Agent
from superagentx.browser_engine import BrowserEngine
from superagentx.llm import LLMClient
from superagentx.prompt import PromptTemplate

logger = logging.getLogger(__name__)

'''
 Run Pytest:  

   1. pytest -s --log-cli-level=INFO tests/browser/everest_masala.py::TestEverestMasalaExtractAgent::test_generation_agent
'''


@pytest.fixture
def agent_client_init() -> dict:
    llm_config = {'model': 'gpt-4o', 'llm_type': 'openai'}

    llm_client: LLMClient = LLMClient(llm_config=llm_config)
    response = {'llm': llm_client, 'llm_type': 'openai'}
    return response


class ExcelHandler(BaseHandler):

    def __init__(
            self
    ):
        super().__init__()

    @tool
    async def excel_writer(
            self,
            result: list[dict]
    ):
        """
        Writes the given result data to an Excel file asynchronously.

        This method accepts a list of dictionaries, where each dictionary represents a row,
        and the keys of the dictionaries represent the column headers.

        Example:
            result = [
                {"Name": "Alice", "Age": 30},
                {"Name": "Bob", "Age": 25}
            ]

        Args:
            result (list[dict]): A list of dictionaries containing tabular data to be written
                                 into an Excel spreadsheet. Each dictionary should have consistent keys.

        """

        import pandas as pd
        path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "sagentx_excel_path"
        )
        df = pd.DataFrame(result)
        df.to_excel(f"{path}/sagentx.xlsx", index=False)
        return "Saved in " + f"{path}/sagentx.xlsx"


class TestEverestMasalaExtractAgent:

    @pytest.mark.filterwarnings("ignore::UserWarning")
    async def test_generation_agent(self, agent_client_init: dict):
        llm_client: LLMClient = agent_client_init.get('llm')

        prompt_template = PromptTemplate()

        browser_engine = BrowserEngine(
            llm=llm_client,
            prompt_template=prompt_template,
            take_screenshot=True
            # browser_instance_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
        )

        goal = """Complete the user's input."""

        marketing_agent = Agent(
            goal=goal,
            role="You are the AI Assistant",
            llm=llm_client,
            prompt_template=prompt_template,
            max_retry=1,
            engines=[browser_engine]
        )

        task = """
        Extract the Everest Masala data from E-Commerce Site. Follow the instructions
        
        Instructions:
        
        1. Go to the any one e-commere website(e.g. Amazon, Flipkart, D-Mart and etc)
        2. Search the Everest Masala in the E-Commerce Site.
        3. Extract the available everest masala data from website. Extract Name, Price, Quantity and Rating
        4. Give me as JSON format.
        """

        query_instruction = task

        result = await marketing_agent.execute(
            query_instruction=query_instruction
        )
        logger.info(f'Result ==> {result}')
        assert result
