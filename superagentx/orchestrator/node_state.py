from enum import Enum


class NodeState(str, Enum):
    """
    Tracks the life-cycle states of individual execution nodes within the DAG.
    """
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
