class PipeStatus:
    PENDING = "Pending"
    RUNNING = "Running"
    COMPLETED = "Completed"
    FAILED = "Failed"

    ALL = {PENDING, RUNNING, COMPLETED, FAILED}


class AgentStatus:
    PENDING = "Pending"
    RUNNING = "Running"
    COMPLETED = "Completed"
    FAILED = "Failed"
    SKIPPED = "Skipped"

    ALL = {PENDING, RUNNING, COMPLETED, FAILED, SKIPPED}
