from superagentx.pipe import AgentXPipe


class BasePipeImpl:

    def __init__(
            self,
            *,
            agentx_pipe: AgentXPipe
    ):
        self.agentx_pipe = agentx_pipe
