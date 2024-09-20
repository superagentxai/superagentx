from abc import ABCMeta, abstractmethod


class Client(metaclass=ABCMeta):

    def __init__(self):
        super().__init__()

    @abstractmethod
    def chat_completion(
            self,
            *args,
            **kwargs
    ):
        pass

    @abstractmethod
    async def achat_completion(
            self,
            *args,
            **kwargs
    ):
        pass

    @abstractmethod
    def embed(self, text, **kwargs):
        """
        Get the embedding for the given text using Client.

        Args:
            text (str): The text to embed.

        Returns:
            list: The embedding vector.
        """
        raise NotImplementedError

    @abstractmethod
    async def aembed(self, text, **kwargs):
        """
        Get the embedding for the given text using Client.

        Args:
            text (str): The text to embed.

        Returns:
            list: The embedding vector.
        """
        raise NotImplementedError
