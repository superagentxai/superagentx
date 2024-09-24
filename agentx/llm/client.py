from abc import ABCMeta, abstractmethod

from pydantic import typing


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
    async def get_tool_json(
            self,
            func: typing.Callable) -> dict:

        pass
