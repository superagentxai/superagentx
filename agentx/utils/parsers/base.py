import abc


class BaseParser(abc.ABC):

    @abc.abstractmethod
    async def parse(self):
        raise NotImplementedError
