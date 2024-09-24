from abc import ABCMeta, abstractmethod


class Client(metaclass=ABCMeta):

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
    def embed(
            self,
            text: str,
            **kwargs
    ):
        """
        Get the embedding for the given text using Client.

        Args:
            text (str): The text to embed.

        Returns:
            list: The embedding vector.
        """
        raise NotImplementedError

    @abstractmethod
    async def aembed(
            self,
            text: str,
            **kwargs
    ):
        """
        Get the embedding for the given text using Client.

        Args:
            text (str): The text to embed.

        Returns:
            list: The embedding vector.
        """
        raise NotImplementedError
