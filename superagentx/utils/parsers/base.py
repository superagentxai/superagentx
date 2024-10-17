import abc


class BaseParser(abc.ABC):

    @abc.abstractmethod
    async def parse(self, *args, **kwargs):
        raise NotImplementedError

    @abc.abstractmethod
    async def get_format_instructions(self) -> str:
        raise NotImplementedError
