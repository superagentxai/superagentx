from superagentx.result import GoalResult


class InvalidType(Exception):
    pass


class ToolError(Exception):
    pass


class StopSuperAgentX(Exception):

    def __init__(
            self,
            message: str,
            goal_result: GoalResult
    ):
        self.message = message
        self.goal_result = goal_result

    def __str__(self):
        return f'StopSuperAgentX: {self.message}'
