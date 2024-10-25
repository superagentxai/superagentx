import abc
import inspect


# Base Class
class BaseHandler(abc.ABC):
    tools = []

    def __init__(self):
        self._get_tools()

    def _get_tools(self) -> list[str]:
        self.tools = []
        for _name, _member in inspect.getmembers(self):
            if inspect.isfunction(_member) or inspect.ismethod(_member):
                if hasattr(_member, '_is_handler_tool') and getattr(_member, '_is_handler_tool'):
                    self.tools.append(_member.__name__)
        return self.tools
