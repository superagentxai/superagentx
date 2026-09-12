from typing import Any, Callable, Dict, List, Optional, Union

from pydantic import BaseModel, Field
from superagentx.orchestrator.node_state import NodeState
from superagentx.result import GoalResult


class RunCheckpoint(BaseModel):
    """
    Pydantic schema representing a complete structural snapshot of a workflow run.
    Enables fault-tolerant checkpoint serialization and process re-hydration.
    """
    run_id: str = Field(description="Unique tracking identifier for the active workflow run pipeline context.")
    states: Dict[str, NodeState] = Field(default_factory=dict,
                                         description="Execution life-cycle state matrix maps per registered node.")
    results: Dict[str, Any] = Field(default_factory=dict,
                                    description="Aggregated execution runtime output data payloads map.")
    global_ctx: Dict[str, Any] = Field(default_factory=dict,
                                       description="Global instruction sets, queries, and environmental settings variables.")
    version: int = Field(default=1,
                         description="Schema structure version control tracking for safe backwards compatibility migrations.")

    goal_results: list[GoalResult] = Field(default_factory=list, description="Goal results for this run.")

    version: int = 0

    approval_node: str | None = None
    approval_status: str | None = None
