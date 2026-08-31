import asyncio
import logging
import uuid
import json
from collections import defaultdict, deque
from typing import Any, Callable, Dict, List, Optional, Union, Set

# SuperAgentX Framework Integrations
from superagentx.agent import Agent
from superagentx.exceptions import StopSuperAgentX
from superagentx.orchestrator.checkpoint import RunCheckpoint
from superagentx.orchestrator.node_state import NodeState
from superagentx.result import GoalResult
from superagentx.router.router_engine import RouterEngine
from superagentx.utils.helper import StatusCallback,_maybe_await


logger = logging.getLogger("SuperAgentX.DAG")




class WorkflowContext:
    """
    Immutable state wrapper context passed strictly to custom operational functional tasks.
    """

    def __init__(self, global_ctx: Dict[str, Any], current_results: Dict[str, Any], states: Dict[str, NodeState]):
        """
        Initializes the functional task read-only workflow boundary tracking context.

        Args:
            global_ctx (Dict[str, Any]): Global instruction keys and configurations map.
            current_results (Dict[str, Any]): Flattened map of all currently completed upstream node outputs.
            states (Dict[str, NodeState]): System life-cycle state tracking matrix map context.
        """
        self.global_ctx = global_ctx
        self._results = current_results
        self._states = states

    def get_output(self, node_name: str) -> Optional[Any]:
        """
        Retrieves the finalized output result string or object of an upstream parent node.

        Args:
            node_name (str): Unique registered structural text identifier name string of the parent target node.

        Returns:
            Optional[Any]: Raw node execution output string, data dict mapping matrix, or None.
        """
        return self._results.get(node_name)

    def get_state(self, node_name: str) -> Optional[NodeState]:
        """
        Retrieves the exact active operational state code metric of a registered target node.

        Args:
            node_name (str): Unique structural text identifier name string of the node.

        Returns:
            Optional[NodeState]: State enum descriptor code metric or None.
        """
        return self._states.get(node_name)


# class InMemoryStore:
#     """
#     Simulates high-speed persistent transactional database round-trips via strict
#     Pydantic JSON model serialization protocols.
#     """
#
#     def __init__(self):
#         """Initializes the underlying volatile textual string data dictionary framework map."""
#         self._storage: Dict[str, str] = {}
#
#     def save(self, checkpoint: RunCheckpoint) -> None:
#         """
#         Serializes and commits an active Pydantic execution snapshot securely into storage.
#
#         Args:
#             checkpoint (RunCheckpoint): Instantiated validated structural snapshot object mapping matrix.
#         """
#         self._storage[checkpoint.run_id] = checkpoint.model_dump_json()
#
#     def load(self, run_id: str) -> Optional[RunCheckpoint]:
#         """
#         Re-hydrates and parses valid serialized JSON strings back into active Pydantic tracking models.
#
#         Args:
#             run_id (str): Unique execution tracking string lookup token.
#
#         Returns:
#             Optional[RunCheckpoint]: Hydrated data tracking class model or None if index lookup bounds fail.
#         """
#         raw_json = self._storage.get(run_id)
#         if not raw_json:
#             return None
#         return RunCheckpoint.model_validate_json(raw_json)


class WorkflowBlueprint:
    """
    Maintains the architectural structural rules mapping, graph paths, configurations,
    and dependency constraints definitions for the execution DAG topology.
    """

    def __init__(self, name: str):
        """
        Initializes the blueprint definition landscape context map layer.

        Args:
            name (str): Descriptive administrative tracking label name identifier string.
        """
        self.name: str = name
        self.nodes: Dict[str, Union[Agent, Callable]] = {}
        self.graph: Dict[str, List[str]] = defaultdict(list)
        self.reverse_graph: Dict[str, List[str]] = defaultdict(list)

    def add_node(self, node: Union[Agent, Callable], name: Optional[str] = None,
                 ) -> None:
        """
        Registers a processing node (SuperAgentX Agent instance or generic async/sync Callable) into the graph.

        Args:
            node (Union[Agent, Callable]): Structural executor element component to register.
            name (Optional[str]): Target string override name tag identifier key.
        """
        node_name = name or getattr(node, "name", getattr(node, "__name__", str(node)))
        self.nodes[node_name] = node

        logger.debug(f"Registered Node blueprint reference: [{node_name}]")

    def add_path(self, *sequence: Union[str, List[str]]) -> None:
        """
        Constructs deterministic path lines between node layers. Accepts strings or parallel lists of nodes.

        Args:
            *sequence (Union[str, List[str]]): Sequential order structures linking parent entities to children arrays.
        """
        for i in range(len(sequence) - 1):
            srcs = [sequence[i]] if isinstance(sequence[i], str) else sequence[i]
            dsts = [sequence[i + 1]] if isinstance(sequence[i + 1], str) else sequence[i + 1]
            for src in srcs:
                for dst in dsts:
                    if dst not in self.graph[src]:
                        self.graph[src].append(dst)
                        self.reverse_graph[dst].append(src)


class AgentXDag:
    """
    Advanced production Asynchronous Topological Multi-Agent Workflow Execution Engine.
    Implements non-blocking dynamic queue resolution pipelines coupled with fault-containment gates.
    """

    def __init__(
            self,
            *,
            blueprint: WorkflowBlueprint,
            # store: InMemoryStore,
            pipe_id: Optional[str] = None,
            name: Optional[str] = None,
            description: Optional[str] = None,
            router: Optional[RouterEngine] = None,
            memory: Optional[Any] = None,
            stop_if_goal_not_satisfied: bool = False,
            workflow_store: bool = False,
            stop_on_node_failure: bool = True
    ):
        """
        Configures the advanced architectural properties of the graph runtime loop execution framework.

        Args:
            blueprint (WorkflowBlueprint): Graph structural path layout routing blueprint rule definitions container.
            store (InMemoryStore): Snapshot check-pointing transaction serialization DB database context.
            pipe_id (Optional[str]): Execution interface instance tracking token string. Autogenerated if omitted.
            name (Optional[str]): Administrative logging string name metric framework identifier label.
            description (Optional[str]): Documented descriptive purpose metadata block content context rules.
            agents (Optional[List]): Collection list tracking system for localized group instances.
            router (Optional[RouterEngine]): Dynamic routing evaluation module for conditional execution paths.
            memory (Optional[Any]): Chat history or configuration storage system injection.
            stop_if_goal_not_satisfied (bool): Direct framework flag mapped to internal Agent verification loop hooks.
            workflow_store (bool): Persists high-level systemic pipeline context states flags.
            stop_on_node_failure (bool): If True, any node error forces immediate global teardown of active parallel tasks.
        """
        self.bp = blueprint
        # self.store = store
        self.pipe_id = pipe_id or uuid.uuid4().hex
        self.name = name or f'{self.__str__()}-{self.pipe_id}'
        self.description = description
        # self.agents = agents or []
        self.router = router
        self.memory = memory
        self.workflow_store = workflow_store
        self.storage = None
        self.stop_if_goal_not_satisfied = stop_if_goal_not_satisfied
        self.stop_on_node_failure = stop_on_node_failure

        logger.debug(f'Initiating AgentXDag Engine Run context for pipeline tracking ID: {self.pipe_id}')

    def __str__(self) -> str:
        return "AgentXDag"

    def _unblock_children(self, node: str, runtime_indegree: Dict[str, int], ready_queue: deque) -> None:
        """
        Reduces the in-degree score metrics of child nodes and queues newly unblocked targets.

        Args:
            node (str): The completed parent node identifier.
            runtime_indegree (Dict[str, int]): Active runtime counter mapping matrix dictionary tracking in-degrees.
            ready_queue (deque): The scheduler processing queue container thread pool tracking element arrays.
        """
        for child in self.bp.graph[node]:
            runtime_indegree[child] -= 1
            if runtime_indegree[child] == 0:
                ready_queue.append(child)

    @staticmethod
    def _extract_output(val: Any) -> str:
        """
        Extracts structural text context string strings out of varying object layers or complex models.

        Args:
            val (Any): Raw node response result payload object structure.

        Returns:
            str: Flat clean Markdown formatted payload string context data to feed downstream prompts.
        """
        if val is None:
            return ""

        # Handle SuperAgentX dynamic structural Pydantic GoalResult objects
        if hasattr(val, "__class__") and val.__class__.__name__ == "GoalResult":
            # If content is None, fall back to the actual GoalResult.result.
            raw_data = getattr(val, "content", None)

            if raw_data is None:
                raw_data = getattr(val, "result", "")

            while isinstance(raw_data, list) and len(raw_data) > 0:
                raw_data = raw_data[0]

            # Unpack nested OpenAI / LiteLLM Completion structure elements
            if hasattr(raw_data, "choices") and isinstance(raw_data.choices, list) and len(raw_data.choices) > 0:
                choice = raw_data.choices[0]
                if hasattr(choice, "message") and hasattr(choice.message, "content"):
                    return str(choice.message.content or "")

            if isinstance(raw_data, (dict, list)):
                return json.dumps(raw_data, indent=2)

            return str(raw_data) if raw_data is not None else ""

        if isinstance(val, str):
            return val

        return str(val)

    def _resolve_previous_agent_result(
        self,
        node: str,
        results: Dict[str, Any],
        goal_results: List[GoalResult],
    ) -> Optional[Any]:
        """
        Resolve previous agent result(s).

        Single parent:
            Return GoalResult.result directly.

        Multiple/parallel parents:
            Preserve the original DAG behavior by collecting each upstream
            result into a labeled text block and joining the blocks.
        """
        parents = self.bp.reverse_graph.get(node, [])

        if not parents:
            return None

        # Single upstream parent.
        if len(parents) == 1:
            parent = parents[0]
            raw_val = results.get(parent)

            logger.info(
                "Resolving previous agent result | "
                "node=%s parent=%s raw_type=%s",
                node,
                parent,
                type(raw_val).__name__,
            )

            if raw_val is None:
                logger.warning(
                    "Previous agent result is missing | "
                    "node=%s parent=%s available_results=%s",
                    node,
                    parent,
                    list(results.keys()),
                )
                return None

            if isinstance(raw_val, GoalResult):
                goal_results.append(raw_val)
                previous_result = raw_val.result

                logger.info(
                    "Using GoalResult.result | "
                    "node=%s parent=%s result_type=%s",
                    node,
                    parent,
                    type(previous_result).__name__,
                )

                return previous_result

            # Handle serialized/deserialized GoalResult.
            if isinstance(raw_val, dict) and "result" in raw_val:
                return raw_val.get("result")

            return raw_val

        # Multiple / parallel upstream parents.
        #
        # Preserve the original parallel contract:
        #
        # ### Output from Upstream Agent [Agent A]:
        # result A
        #
        # ### Output from Upstream Agent [Agent B]:
        # result B
        #
        # The source is now GoalResult.result instead of _extract_output().
        context_blocks: List[str] = []

        for parent in parents:
            raw_val = results.get(parent)

            if raw_val is None:
                logger.warning(
                    "Missing result for upstream parent | "
                    "node=%s parent=%s",
                    node,
                    parent,
                )
                continue

            if isinstance(raw_val, GoalResult):
                goal_results.append(raw_val)
                parent_result = raw_val.result

            elif isinstance(raw_val, dict) and "result" in raw_val:
                parent_result = raw_val.get("result")

            else:
                parent_result = raw_val

            if parent_result is None:
                continue

            if isinstance(parent_result, str):
                parent_output = parent_result
            elif isinstance(parent_result, (dict, list)):
                parent_output = json.dumps(
                    parent_result,
                    indent=2,
                    default=str,
                )
            else:
                parent_output = str(parent_result)

            context_blocks.append(
                f"### Output from Upstream Agent [{parent}]:\n"
                f"{parent_output}"
            )

            logger.info(
                "Parallel upstream result collected | "
                "node=%s parent=%s result_type=%s",
                node,
                parent,
                type(parent_result).__name__,
            )

        return "\n\n".join(context_blocks) if context_blocks else None


    async def _emit_checkpoint(
            self,
            *,
            checkpoint: RunCheckpoint,
            run_id: str,
            node: str | None,
            status_callback: Optional[StatusCallback],
    ) -> None:
        """
        Publish the current workflow checkpoint through the existing
        status_callback -> RabbitMQ pipeline.
        """

        checkpoint.version += 1

        if not status_callback:
            return

        node_item = (
            self.bp.nodes.get(node)
            if node is not None
            else None
        )

        checkpoint_message = {
            "event": "workflow_checkpoint",
            "run_id": run_id,
            "pipe_id": self.pipe_id,
            "node": node,
            "agent_id": (
                getattr(node_item, "agent_id", None)
                if node_item is not None
                else None
            ),
            "agent": (
                getattr(node_item, "name", node)
                if node_item is not None
                else node
            ),
            "checkpoint_version": checkpoint.version,
            "checkpoint": checkpoint.model_dump(
                mode="json"
            ),
        }

        logger.info(
            "Publishing workflow_checkpoint: "
            "run_id=%s version=%s node=%s",
            run_id,
            checkpoint.version,
            node,
        )

        await _maybe_await(
            status_callback(**checkpoint_message)
        )

    async def execute(
            self,
            run_id: str,
            verify_goal: bool = True,
            conversation_id: str | None = None,
            initial_ctx: Optional[Dict[str, Any]] = None,
            status_callback: Optional[StatusCallback] = None,
            checkpoint: RunCheckpoint | None = None,
    ) -> RunCheckpoint:
        """
        Executes the entire structural workflow pipeline using real-time fluid queue calculations.
        Intercepts thread operations seamlessly when exceptions are detected or conditional policy rules shift.

        Args:
            run_id (str): Persistent unique operational run token string identifier targeting the tracking run sequence.
            initial_ctx (Optional[Dict[str, Any]]): Root instruction metrics, instructions, queries, and setups.
            status_callback (Optional[StatusCallback]): Framework user-experience telemetry tracking module.

        Returns:
            Dict[str, NodeState]: A comprehensive state matrix layout detailing the lifecycle outcomes of all nodes.

        Raises:
            Exception: Escalates unexpected unrecoverable programmatic runtime system core failures if global teardown flags are bypassed.
        """
        goal_results: list[GoalResult] = []

        if checkpoint is None:
            checkpoint = RunCheckpoint(
                run_id=run_id,
                states={
                    node: NodeState.PENDING
                    for node in self.bp.nodes
                },
                global_ctx=initial_ctx or {},
            )

            await self._emit_checkpoint(
                checkpoint=checkpoint,
                run_id=run_id,
                node=None,
                status_callback=status_callback,
            )

        states = checkpoint.states
        results = checkpoint.results
        global_ctx = checkpoint.global_ctx

        tasks: Dict[asyncio.Task, str] = {}
        runtime_indegree = {node: len(self.bp.reverse_graph[node]) for node in self.bp.nodes}

        # Fast-forward path topology checks using completed/skipped states from prior checkpoints
        for node in self.bp.nodes:
            current_node_state: NodeState = states.get(node, NodeState.PENDING)
            if current_node_state in (NodeState.COMPLETED, NodeState.SKIPPED):
                for child in self.bp.graph[node]:
                    runtime_indegree[child] -= 1

        ready_queue = deque([
            n for n in self.bp.nodes
            if runtime_indegree.get(n, 0) == 0 and states.get(n) in (NodeState.PENDING, NodeState.RUNNING)
        ])

        abort_pipeline = False

        # 2. Asynchronous Event-Driven Process Loop Architecture
        while (ready_queue or tasks) and not abort_pipeline:
            while ready_queue and not abort_pipeline:
                node = ready_queue.popleft()

                # 3. Upstream Failure / Action Policy Processing Checks
                parent_policy_passed = True
                for parent in self.bp.reverse_graph[node]:
                    if states.get(parent) in (NodeState.SKIPPED, NodeState.FAILED):
                        parent_policy_passed = False
                    elif states.get(parent) == NodeState.COMPLETED and results.get(parent) == "POLICY_FAILED":
                        parent_policy_passed = False

                if not parent_policy_passed:
                    states[node] = NodeState.SKIPPED
                    await self._emit_checkpoint(
                        checkpoint=checkpoint,
                        run_id=run_id,
                        node=node,
                        status_callback=status_callback,
                    )
                    logger.info(f"  Skipping Node '{node}' due to upstream pipeline conditions.")
                    self._unblock_children(node, runtime_indegree, ready_queue)
                    continue

                # states[node] = NodeState.RUNNING

                node_item = self.bp.nodes[node]

                # ---------------------------------------------------------
                # Resolve upstream agent output BEFORE policy authorization.
                #
                # The policy/context builder may depend on the previous
                # agent's result. Previously this value was calculated only
                # after _authorize(), which caused downstream authorization
                # requests to receive previous_agent_result=None.
                # ---------------------------------------------------------
                previous_agent_result = None

                if isinstance(node_item, Agent):
                    previous_agent_result = self._resolve_previous_agent_result(
                        node=node,
                        results=results,
                        goal_results=goal_results,
                    )

                    logger.info(
                        "Resolved previous_agent_result | "
                        "node=%s type=%s value=%r",
                        node,
                        type(previous_agent_result).__name__,
                        previous_agent_result,
                    )

                # ---------------------------------------------------------
                # 5. APPROVAL DECISION
                # ---------------------------------------------------------

                approval_granted = (
                        checkpoint.approval_status == "APPROVED"
                        and checkpoint.approval_node == node
                )

                approval_required = False

                if isinstance(node_item, Agent):

                    # -----------------------------------------------------
                    # POLICY PRE-AUTHORIZATION
                    #
                    # Only evaluate policy when this node has NOT already
                    # received human approval.
                    # -----------------------------------------------------
                    if not approval_granted:

                        try:
                            policy_decision = await node_item._authorize(
                                query_instruction=global_ctx.get(
                                    "query_instruction",
                                    ""
                                ),
                                pipe_id=self.pipe_id,
                                conversation_id=conversation_id,
                                previous_agent_result=previous_agent_result,
                            )

                        except PermissionError as ex:

                            logger.warning(
                                "Policy denied node '%s': %s",
                                node,
                                ex,
                            )

                            states[node] = NodeState.FAILED
                            results[node] = "POLICY_FAILED"

                            await self._emit_checkpoint(
                                checkpoint=checkpoint,
                                run_id=run_id,
                                node=node,
                                status_callback=status_callback,
                            )

                            if self.stop_on_node_failure:
                                abort_pipeline = True

                            break

                        policy_requires_approval = (
                                policy_decision is not None
                                and policy_decision.decision == "APPROVE"
                        )

                        if policy_requires_approval:
                            approval_required = True

                            logger.info(
                                "[APPROVAL_REQUIRED] "
                                "run_id=%s, node=%s, reason=POLICY_APPROVE",
                                run_id,
                                node,
                            )

                    else:

                        # Human approval was already granted for this exact node.
                        logger.info(
                            "Skipping policy pre-authorization for node='%s' "
                            "because approval_granted=True",
                            node,
                        )

                    # -----------------------------------------------------
                    # HUMAN APPROVAL
                    # -----------------------------------------------------
                    if approval_required and not approval_granted:

                        states[node] = NodeState.WAITING_FOR_APPROVAL

                        checkpoint.approval_node = node
                        checkpoint.approval_status = "WAITING"
                        checkpoint.goal_results = goal_results

                        logger.info(
                            "🔥 BEFORE APPROVAL CHECKPOINT | "
                            "run_id=%s node=%s version=%s status_callback=%s",
                            run_id,
                            node,
                            checkpoint.version,
                            status_callback is not None,
                        )

                        await self._emit_checkpoint(
                            checkpoint=checkpoint,
                            run_id=run_id,
                            node=node,
                            status_callback=status_callback,
                        )

                        logger.info(
                            "[WAITING_FOR_APPROVAL] "
                            "run_id=%s node=%s",
                            run_id,
                            node,
                        )

                        return checkpoint

                # ---------------------------------------------------------
                # 6. START NODE EXECUTION
                # ---------------------------------------------------------

                states[node] = NodeState.RUNNING

                await self._emit_checkpoint(
                    checkpoint=checkpoint,
                    run_id=run_id,
                    node=node,
                    status_callback=status_callback,
                )

                ctx = WorkflowContext(
                    global_ctx,
                    results.copy(),
                    states.copy()
                )
                # 5. Native Dynamic Dispatch Architecture
                if isinstance(node_item, Agent):
                    # previous_agent_result was resolved before authorization
                    # and is reused here for actual agent execution.
                    approval_granted = (
                            checkpoint.approval_status == "APPROVED"
                            and checkpoint.approval_node == node
                    )

                    # Dynamic Framework Method Signature Packaging Alignment
                    task = asyncio.create_task(
                        node_item.execute(
                            query_instruction=global_ctx.get("query_instruction", ""),
                            pipe_id=self.pipe_id,
                            pre_result=global_ctx.get("pre_result", []),
                            previous_agent_result=previous_agent_result,
                            verify_goal=verify_goal,
                            stop_if_goal_not_satisfied=self.stop_if_goal_not_satisfied,
                            conversation_id=conversation_id,
                            storage=self.storage,
                            status_callback=status_callback,
                            approval_granted=approval_granted,

                        )
                    )
                else:
                    task = asyncio.create_task(node_item(ctx))

                tasks[task] = node

            if not tasks:
                break

            # 6. Optimized Event Loop Worker Processing Pool Allocation
            done, _ = await asyncio.wait(tasks.keys(), return_when=asyncio.FIRST_COMPLETED)

            for task in done:
                node = tasks.pop(task)
                try:
                    results[node] = await task

                    logger.info(
                        "Node result stored | "
                        "node=%s type=%s result=%r",
                        node,
                        type(results[node]).__name__,
                        results[node],
                    )

                    states[node] = NodeState.COMPLETED

                    await self._emit_checkpoint(
                        checkpoint=checkpoint,
                        run_id=run_id,
                        node=node,
                        status_callback=status_callback,
                    )

                    logger.debug(
                        "Node '%s' completed. Output is now available in "
                        "checkpoint.results for downstream authorization.",
                        node,
                    )

                    self._unblock_children(node, runtime_indegree, ready_queue)
                except (Exception, StopSuperAgentX) as e:
                    # 7. Granular Node Isolation and Containment Handling
                    states[node] = NodeState.FAILED
                    results[node] = getattr(e, "goal_result", f"Error structural exception trace: {str(e)}")
                    await self._emit_checkpoint(
                        checkpoint=checkpoint,
                        run_id=run_id,
                        node=node,
                        status_callback=status_callback,
                    )
                    logger.error(f" Execution crash localized on Node identity marker [{node}]: {e}")

                    if self.stop_on_node_failure:
                        logger.critical(
                            " 'stop_on_node_failure' flag active. Launching immediate global framework shutdown pipeline sequence.")
                        abort_pipeline = True
                        break

            # 8. Transmit Transaction Checks Interceptive & Persist Securely
            if abort_pipeline:
                # Cancel all remaining active in-flight parallel operations securely
                for active_task in list(tasks.keys()):
                    active_task.cancel()

                if tasks:
                    await asyncio.gather(*tasks.keys(), return_exceptions=True)

                # Transition all remaining unprocessed workflow states cleanly into a containment error state
                for remaining_node in self.bp.nodes:
                    if states[remaining_node] in (NodeState.PENDING, NodeState.RUNNING):
                        states[remaining_node] = NodeState.FAILED

                await self._emit_checkpoint(
                    checkpoint=checkpoint,
                    run_id=run_id,
                    node=None,
                    status_callback=status_callback,
                )

                break

            # Save GoalResults from all agents
            checkpoint.goal_results = goal_results
            # await self._emit_checkpoint(
            #     checkpoint=checkpoint,
            #     run_id=run_id,
            #     node=None,
            #     status_callback=status_callback,
            # )

            print(f"CHECKPOINT SAVE STATE: {checkpoint}")

        return checkpoint

    async def resume(
            self,
            run_id: str,
            *,
            checkpoint: dict,
            conversation_id: str | None = None,
            status_callback: Optional[StatusCallback] = None,
    ) -> Dict[str, NodeState]:

        checkpoint_model = RunCheckpoint.model_validate(
            checkpoint
        )

        if checkpoint_model.run_id != run_id:
            raise ValueError(
                "run_id does not match checkpoint.run_id"
            )

        if checkpoint_model.approval_status != "APPROVED":
            raise ValueError(
                f"Workflow is not approved for run_id={run_id}"
            )

        node = checkpoint_model.approval_node

        if not node:
            raise ValueError(
                f"Approved node missing for run_id={run_id}"
            )

        logger.info(
            "Resuming run_id=%s node=%s",
            run_id,
            node,
        )

        checkpoint_model.states[node] = NodeState.PENDING

        return await self.execute(
            run_id=run_id,
            checkpoint=checkpoint_model,
            conversation_id=conversation_id,
            status_callback=status_callback,
        )

    async def reject(
            self,
            *,
            run_id: str,
            checkpoint: dict,
    ):
        checkpoint_model = RunCheckpoint.model_validate(checkpoint)

        checkpoint_model.approval_status = "REJECTED"

        for node, state in checkpoint_model.states.items():
            if state == NodeState.WAITING_FOR_APPROVAL:
                checkpoint_model.states[node] = NodeState.FAILED

        return checkpoint_model.states