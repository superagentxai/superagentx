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
