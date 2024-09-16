from abc import ABCMeta


class BaseEmbeddings(metaclass=ABCMeta):

    def __init__(self):
        super().__init__()

    def embed(self, text, **kwargs):
        """
        Get the embedding for the given text using OpenAI.

        Args:
            text (str): The text to embed.

        Returns:
            list: The embedding vector.
        """
        raise NotImplementedError

    async def aembed(self, text, **kwargs):
        """
        Get the embedding for the given text using OpenAI.

        Args:
            text (str): The text to embed.

        Returns:
            list: The embedding vector.
        """
        raise NotImplementedError
