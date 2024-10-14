import wikipedia

from agentx.handler.base import BaseHandler
from agentx.handler.wikipedia.exceptions import InvalidAction
from agentx.utils.helper import sync_to_async


class WikipediaHandler(BaseHandler):
    """
        A handler class for managing interactions with the Wikipedia API.
        This class extends BaseHandler and provides methods for retrieving and processing content
        from Wikipedia, including searching articles, fetching summaries, and accessing structured data.
    """

    async def get_summary(self,
                          query: str,
                          sentences: int = None,
                          language: str = None
                          ):

        """
        Asynchronously retrieves a summary of a specified topic or content.
        This method condenses information into a concise format, making it easier to understand key points at a glance.

        parameter:
            query (str | None, optional): The search query to retrieve relevant information. Defaults to None.
            sentences (int | None, optional): The maximum number of sentences to return in the response. Defaults to None.
            language (str | None, optional): The language code for the response content. Defaults to None.

        """

        if language:
            await sync_to_async(wikipedia.set_lang, language)

        return await sync_to_async(wikipedia.summary, query, sentences=sentences)

    async def get_search(self,
                         query: str,
                         results: int,
                         language: str
                         ):

        """
        Asynchronously performs a search operation based on the specified parameters.
        This method retrieves relevant results based on the query and other filters, such as language and result limits.

        parameter:
            query (str | None, optional): The search query to retrieve relevant information. Defaults to None.
            results (int | None, optional): The maximum number of results to return. Defaults to None, indicating
            no limit on the number of results.
            language (str | None, optional): The language code for the response content. Defaults to None.

        """

        if language:
            await sync_to_async(wikipedia.set_lang, language)

        return await sync_to_async(wikipedia.search, query, results=results)

    def __dir__(self):
        return (
            'get_summary',
            'get_search'
        )
