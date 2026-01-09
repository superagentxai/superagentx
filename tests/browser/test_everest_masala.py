import os
import warnings

from aiopath import AsyncPath

from superagentx.agentxpipe import AgentXPipe
from superagentx.computer_use.browser.browser import Browser, BrowserConfig
from superagentx.engine import Engine
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
   1. pytest -s --log-cli-level=INFO tests/browser/test_everest_masala.py::TestEverestMasalaExtractAgent::test_generation_agent
'''


@pytest.fixture
def agent_client_init() -> dict:
    llm_config = {'model': 'gpt-5.1', 'llm_type': 'openai'}

    llm_client: LLMClient = LLMClient(llm_config=llm_config)
    response = {'llm': llm_client, 'llm_type': 'openai'}
    return response


class DataWriterHandler(BaseHandler):

    def __init__(
            self
    ):
        super().__init__()

    @tool
    async def excel_writer(
            self,
            data: list
    ):
        """
        Saves the given data into an Excel file without blocking other actions.
        This method accepts a list of dictionaries, where each dictionary represents a row,
        and the keys of the dictionaries represent the column headers.
        Example:
            data = [
                {"Name": "Alice", "Age": 30},
                {"Name": "Bob", "Age": 25}
            ]
        Args:
            @param data: A list of dictionaries containing tabular data to be written into an Excel spreadsheet.
             Each dictionary should have consistent keys.
        """

        import pandas as pd
        path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "sagentx_excel_path"
        )
        _path = AsyncPath(path)
        if not await _path.exists():
            os.makedirs(path)

        if data:
            df = pd.DataFrame(data)
            df.to_excel(f"{path}/sagentx.xlsx", index=False)
            return "Saved in " + f"{path}/sagentx.xlsx"
        return "Failed to write data in excel"

    @tool
    async def csv_writer(
            self,
            data: list
    ):
        """
        Saves the given data into an CSV file without blocking other actions.
        This method accepts a list of dictionaries, where each dictionary represents a row,
        and the keys of the dictionaries represent the column headers.
        Example:
            data = [
                {"Name": "Alice", "Age": 30},
                {"Name": "Bob", "Age": 25}
            ]
        Args:
            @param data: A list of dictionaries containing tabular data to be written into an CSV.
            Each dictionary should have consistent keys.
        """

        import pandas as pd
        path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "sagentx_excel_path"
        )
        _path = AsyncPath(path)
        if not await _path.exists():
            os.makedirs(path)

        if data:
            df = pd.DataFrame(data)
            df.to_csv(f"{path}/sagentx.csv", index=False)
            return "Saved in " + f"{path}/sagentx.csv"
        return "Failed to write data in csv"


class TestEverestMasalaExtractAgent:

    @pytest.mark.asyncio
    @pytest.mark.filterwarnings("ignore::UserWarning")
    async def test_generation_agent(self, agent_client_init: dict):
        llm_client: LLMClient = agent_client_init.get('llm')

        prompt_template = PromptTemplate()
        excel_prompt = PromptTemplate(
            system_message="""
                    Write a data from previous agent's result in excel and csv.
                    """
        )

        excel_handler = DataWriterHandler()

        excel_engine = Engine(
            llm=llm_client,
            prompt_template=excel_prompt,
            handler=excel_handler
        )
        browser = Browser(config=BrowserConfig(headless=False, disable_security=True, browser_type='firefox'))
        browser_engine = BrowserEngine(
            llm=llm_client,
            prompt_template=prompt_template,
            take_screenshot=True,
            # browser=browser
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

        excel_agent = Agent(
            goal="Write a data in excel sheet and csv and save it from previous agent's result. Make sure keep the "
                 "previous agent's result. It should pass into the tools.",
            role="You are Excel and csv Expert",
            llm=llm_client,
            prompt_template=excel_prompt,
            max_retry=1,
            engines=[excel_engine],
            human_approval=True
        )

        task = """
        Extract the Everest Masala data from E-Commerce Site. Follow the instructions

        Instructions:

        1. Go to the any one e-commere website(e.g. Amazon, Flipkart, D-Mart and etc)
        2. Search the Everest Masala in the E-Commerce Site.
        3. Extract the available everest masala data from website. Extract Name, Price, Quantity and Rating
        4. Give me as JSON format.
        """

        pipe = AgentXPipe(
            agents=[marketing_agent, excel_agent]
        )

        result = await pipe.flow(
            query_instruction=task
        )
        logger.info(f'Result ==> {result}')
        assert result
