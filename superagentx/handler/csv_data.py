import asyncio
import re
import logging
import pandas as pd

from superagentx.handler.base import BaseHandler
from superagentx.llm import LLMClient, ChatCompletionParams

logger = logging.getLogger(__name__)

class CsvHandler(BaseHandler):

    def __init__(
            self,
            *,
            csv_path: str,
            llm_client: LLMClient | None = None,
            prompt: str | None = None
    ):
        self.input = csv_path
        self.llm_client: LLMClient = llm_client
        self.prompt = prompt

        if not self.llm_client:
            llm_config = {'llm_type': 'openai'}
            self.llm_client: LLMClient = LLMClient(llm_config=llm_config)

    async def search(self,
                     query: str
                     ):
        """
        A search operation using the provided query string. This method initiates an asynchronous search based on
        the input `query` and returns the search results. The actual behavior and data source of the search
        (e.g., a database, an API, or a local cache) depend on the underlying implementation.

        Args:
            query (str):
                The search term or query string used to retrieve relevant results. This can be a keyword, a phrase,
                or any other string that specifies what to search for.
        """

        try:
            prompt = self.prompt
            if not prompt:
                df = pd.read_csv(self.input)
                prompt = (f"Given the following CSV data columns: {list(df.columns)},"
                          f"generate a filter condition based on the query: '{query}'."
                          f"Example:\n df[(df['Index'] >= 10) & (df['Index'] <= 15)]")
            messages = [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            chat_completion_params = ChatCompletionParams(
                messages=messages,
                temperature=0
            )
            response = await self.llm_client.achat_completion(
                chat_completion_params=chat_completion_params
            )
            result = response.choices[0].message.content.strip()
            start = '```python\n'
            end = '```'
            trim_res = re.findall(re.escape(start) + "(.+?)" + re.escape(end), result, re.DOTALL)
            return eval(trim_res[0]).to_json()
        except Exception as ex:
            message = f"Error while searching result! {ex}"
            logger.error(message)
            raise Exception(message)

    def __dir__(self):
        return (
            'search',
        )
