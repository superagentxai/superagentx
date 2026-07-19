from superagentx.handler.base import BaseHandler
from superagentx.handler.decorators import tool


class MathToolHandler(BaseHandler):
    """
    Custom tool handler providing real mathematical execution parameters
    to SuperAgentX agents.
    """

    def __init__(self):
        super().__init__()

    @tool
    async def calculate_addition(self, a: float, b: float) -> str:
        """
        Executes arithmetic addition on two numerical values.

        Args:
            a (float): The first value or addend.
            b (float): The second value or addend.
        Returns:
            str: A formatted calculation result string.
        """
        result = a + b
        return f"Calculation Addition Result: {a} + {b} = {result}"

    @tool
    async def calculate_multiplication(self, a: float, b: float) -> str:
        """
        Executes arithmetic multiplication on two numerical values.

        Args:
            a (float): The first factor value.
            b (float): The second factor value.
        Returns:
            str: A formatted calculation result string.
        """
        result = a * b
        return f"Calculation Multiplication Result: {a} * {b} = {result}"