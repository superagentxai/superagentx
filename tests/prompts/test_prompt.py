from agentx.utils.helper import get_fstring_variables
import logging

logger = logging.getLogger(__name__)


class TestPrompt:

    async def test_f_string_parser(self):
        prompt_template = """Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer.


        Question: {question}
        Helpful Answer:"""

        result = await get_fstring_variables(prompt_template)
        logger.info(f"Prompt variables test {type(result)}")
