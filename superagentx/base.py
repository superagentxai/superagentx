from abc import ABC, abstractmethod


class BaseEngine(ABC):
    def __init__(self, *args, **kwargs):
        """
        BaseEngine is an abstract class that defines a common interface for different automation engines.
        """
        pass

    @abstractmethod
    async def start(self, *args, **kwargs):
        """
        Abstract method to execute an action within the engine.
        """
        pass
    