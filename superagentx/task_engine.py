import json
import asyncio
import inspect
import logging
import traceback
import re
from typing import Any, Callable, Dict, List, Awaitable, Optional

from superagentx.base import BaseEngine
from superagentx.db_store import StorageAdapter
from superagentx.handler.base import BaseHandler
from superagentx.result import GoalResult
from superagentx.utils.observability.engine_telemetry_decorator import engine_telemetry

logger = logging.getLogger(__name__)

SAFE_BUILTINS = {
    "len": len,
    "range": range,
    "sum": sum,
    "min": min,
    "max": max,
    "sorted": sorted,
}

# Pre-compiled compiled regex patterns for performance
PATH_SPLIT_RE = re.compile(r"\.(?![^\[]*])")
KEY_EXTRACT_RE = re.compile(r"^([^\[\]]+)")
INDEX_FIND_RE = re.compile(r"\[(\d+)]")
PREV_RE = re.compile(r"\$prev(?:\.([A-Za-z0-9_.\[\]]+))?")
PREV_RESULT_RE = re.compile(r"\$prev_result(?:[\.\[][A-Za-z0-9_.\[\]]+)?")
TOKEN_RE = re.compile(r"\[(\d+)\]|([A-Za-z_][A-Za-z0-9_]*)")
BRACKET_INDEX_RE = re.compile(r"\[(\d+)\]")


def _get_from_path(root: Any, path: str) -> Any:
    """Traverse nested dict/list using dotted + indexed path. (Synchronous utility)"""
    if root is None:
        return None

    cur = root
    parts = PATH_SPLIT_RE.split(path) if path else []

    for part in parts:
        m = KEY_EXTRACT_RE.match(part)
        key = m.group(1) if m else part

        if isinstance(cur, dict):
            cur = cur.get(key)
        else:
            cur = getattr(cur, key, None)

        if cur is None:
            return None

        # Resolve list/tuple indices
        idxs = INDEX_FIND_RE.findall(part)
        for idx in idxs:
            try:
                cur = cur[int(idx)]
            except (IndexError, KeyError, TypeError):
                return None

    return cur


async def _safe_exec(code: str) -> Dict[str, Any]:
    """Executes code safely in a separate thread using a limited builtins set."""

    def _exec_block() -> Dict[str, Any]:
        local_ns: Dict[str, Any] = {}
        try:
            exec(code, {"__builtins__": SAFE_BUILTINS}, local_ns)
            return {"locals": local_ns}
        except Exception as e:
            return {"error": str(e), "traceback": traceback.format_exc()}

    return await asyncio.to_thread(_exec_block)


class TaskEngine(BaseEngine):
    """
    Asynchronous TaskEngine
    - Execute python code (safe mode) and/or run handler methods or tools, all asynchronously.
    - instructions:
        dict → sequential step {"method": {...}}
        list → parallel steps [{"m1": {}}, {"m2": {}}]
    """

    def __init__(
            self,
            *,
            handler: BaseHandler,
            tools: Dict[str, Callable | Awaitable] | None = None,
            code: str | None = None,
            safe_mode: bool = True,
            max_steps: int = 100,
            sensitive_data: Dict[str, str] | None = None,
            instructions: List[Any] | None = None,
            **kwargs,
    ):
        super().__init__(**kwargs)

        self.context: Dict[str, Any] | None = None
        self.handler = handler
        self.tools = tools or {}
        self.code = code
        self.safe_mode = safe_mode
        self.max_steps = max_steps
        self.sensitive_data = sensitive_data or {}
        self.instructions = instructions or []

        # runtime state
        self.results: List[Dict[str, Any]] = []
        self.n_steps = 0
        self.last_result: Dict[str, Any] | None = None

        self._validate_instructions_type()

    def __str__(self) -> str:
        return f"TaskEngine({self.handler.__class__.__name__})"

    # ----------------------------------------------------
    # Validation
    # ----------------------------------------------------
    def _validate_instructions_type(self) -> None:
        if not isinstance(self.instructions, (list, tuple)):
            raise ValueError("instructions must be a list or tuple")

    def _ensure_step_limit(self) -> None:
        if self.n_steps >= self.max_steps:
            raise RuntimeError(f"Max step limit of {self.max_steps} exceeded")

    # ----------------------------------------------------
    # $prev reference resolution (Synchronous utility)
    # ----------------------------------------------------
    def _resolve_prev_reference(self, value: str) -> Any:
        if not self.last_result:
            return None

        m = PREV_RE.search(value)
        if not m:
            return None

        path = m.group(1)
        wrapper = self.last_result

        # Determine inner root
        if "parallel_map" in wrapper:
            inner = wrapper["parallel_map"]
        elif "successes" in wrapper or "failures" in wrapper:
            inner = wrapper
        else:
            try:
                first_val = next(iter(wrapper.values()))
                if isinstance(first_val, dict):
                    if "result" in first_val:
                        inner = first_val["result"]
                    elif "data" in first_val:
                        inner = first_val["data"]
                    else:
                        inner = first_val
                else:
                    inner = first_val
            except StopIteration:
                return None

        if not path:
            return inner

        return _get_from_path(inner, path)

    def _normalize_previous_agent_result(self, result: Any) -> Dict[str, Any]:
        if result is None:
            return {}

        normalized = {}

        def extract(obj):
            if isinstance(obj, dict):
                for method_name, value in obj.items():
                    if (
                            isinstance(value, dict)
                            and value.get("success") is True
                            and "result" in value
                    ):
                        normalized[method_name] = value["result"]
                    else:
                        extract(value)
            elif isinstance(obj, (list, tuple)):
                for item in obj:
                    extract(item)

        extract(result)
        return normalized

    def _resolve_dynamic_params(self, params: Dict[str, Any], previous_agent_result: Optional[Any] = None) -> Dict[str, Any]:
        """Resolve $prev and $prev_result references recursively."""
        normalized_agent_result = self._normalize_previous_agent_result(previous_agent_result)

        def _resolve_prev_result_reference(expr: str) -> Any:
            if expr == "$prev_result":
                return normalized_agent_result

            path = expr[12:]  # len("$prev_result")
            current = normalized_agent_result

            try:
                while path.startswith("["):
                    m = BRACKET_INDEX_RE.match(path)
                    if not m:
                        break
                    current = current[int(m.group(1))]
                    path = path[m.end():]

                if path.startswith("."):
                    path = path[1:]
            except Exception as e:
                logger.error(f"Error while resolving previous result reference: {e}")

            return _get_from_path(current, path)

        def _resolve_string(val: str) -> Any:
            if PREV_RESULT_RE.fullmatch(val):
                return _resolve_prev_result_reference(val)

            if PREV_RE.fullmatch(val):
                return self._resolve_prev_reference(val)

            # Inline replacements
            def replace_prev_result(match):
                full = match.group(0)
                resolved = _resolve_prev_result_reference(full)
                return str(resolved) if resolved is not None else full

            val = PREV_RESULT_RE.sub(replace_prev_result, val)

            def replace_prev(match):
                full = match.group(0)
                resolved = self._resolve_prev_reference(full)
                return str(resolved) if resolved is not None else full

            return PREV_RE.sub(replace_prev, val)

        def _resolve(v: Any) -> Any:
            if isinstance(v, str):
                return _resolve_string(v)
            if isinstance(v, dict):
                return {k: _resolve(sub) for k, sub in v.items()}
            if isinstance(v, list):
                return [_resolve(item) for item in v]
            return v

        return {k: _resolve(v) for k, v in params.items()}

    # ----------------------------------------------------
    # Method Execution
    # ----------------------------------------------------
    async def _execute_method(self, method_name: str, params: Dict[str, Any], previous_agent_result: Optional[Any] = None) -> Dict[str, Any]:
        """Execute a single handler or tool method."""
        self._ensure_step_limit()
        self.n_steps += 1

        func = self.tools.get(method_name) or getattr(self.handler, method_name, None)

        if func is None:
            result = {method_name: {"success": False, "error": f"Method `{method_name}` not found"}}
            self.last_result = result
            return result

        params = self._resolve_dynamic_params(params=params or {}, previous_agent_result=previous_agent_result)
        print(f"Executing {method_name} - params: {params}")

        try:
            if inspect.iscoroutinefunction(func):
                output = await func(**params)
            else:
                output = await asyncio.to_thread(func, **params)

            result = {method_name: {"success": True, "result": output}}
        except Exception as e:
            result = {
                method_name: {
                    "success": False,
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                }
            }

        self.results.append(result)
        self.last_result = result
        return result

    # ----------------------------------------------------
    # Parallel Execution (auto-map + success/failure grouping)
    # ----------------------------------------------------
    async def _run_parallel(self, parallel_steps: List[Dict[str, Any]], previous_agent_result: Optional[Any] = None) -> None:
        """Run multiple steps concurrently using asyncio.gather."""
        tasks = []
        method_names = []

        for step in parallel_steps:
            if not isinstance(step, dict) or len(step) != 1:
                raise ValueError(f"Invalid parallel step: {step}")
            name, params = next(iter(step.items()))
            method_names.append(name)
            tasks.append(self._execute_method(method_name=name, params=params, previous_agent_result=previous_agent_result))

        batch = await asyncio.gather(*tasks)

        parallel_map = {}
        successes = {}
        failures = {}

        for i, method_name in enumerate(method_names):
            step_result = batch[i][method_name]
            if step_result["success"]:
                result_val = step_result["result"]
                parallel_map[method_name] = result_val
                successes[method_name] = result_val
            else:
                parallel_map[method_name] = None
                failures[method_name] = step_result["error"]

        wrapper = {
            "parallel_results": batch,
            "parallel_map": parallel_map,
            "successes": successes,
            "failures": failures
        }

        self.results.append(wrapper)
        self.last_result = wrapper

        self.n_steps += 1
        self._ensure_step_limit()

    # ----------------------------------------------------
    # Sequential Execution
    # ----------------------------------------------------
    async def _run_sequence(self, steps: List[Dict[str, Any]], previous_agent_result: Optional[Any] = None) -> None:
        """Run steps one after another."""
        for step in steps:
            if not isinstance(step, dict) or len(step) != 1:
                raise ValueError(f"Invalid sequence step: {step}")
            name, params = next(iter(step.items()))
            await self._execute_method(method_name=name, params=params, previous_agent_result=previous_agent_result)

    # ----------------------------------------------------
    # Main Execution
    # ----------------------------------------------------
    async def _execute(self, task_agent_input: Optional[Any] = None, pre_result: Optional[Any] = None) -> List[Dict[str, Any]]:
        """Core execution loop for code and instructions."""
        if self.code:
            if self.safe_mode:
                code_output = await _safe_exec(self.code)
            else:
                def _unsafe_exec_block():
                    local_ns: Dict[str, Any] = {}
                    try:
                        exec(self.code, {}, local_ns)
                        return {"locals": local_ns}
                    except Exception as e:
                        return {"error": str(e), "traceback": traceback.format_exc()}

                code_output = await asyncio.to_thread(_unsafe_exec_block)

            self.results.append({"code": code_output})
            self.last_result = {"code": code_output}

            self.n_steps += 1
            self._ensure_step_limit()

        for step in self.instructions:
            if isinstance(step, list):
                await self._run_parallel(parallel_steps=step, previous_agent_result=task_agent_input)
            elif isinstance(step, dict):
                await self._run_sequence(steps=[step], previous_agent_result=task_agent_input)
            else:
                raise ValueError(f"Invalid instruction step: {step}")
        return self.results

    # ----------------------------------------------------
    # Public API
    # ----------------------------------------------------
    @engine_telemetry(
        engine_type="task",
        engine_name_resolver=lambda self, **_: f"{self.handler.__class__.__name__}",
    )
    async def start(
            self,
            input_prompt: str | None = None,
            pipe_id: str | None = None,
            agent_id: str | None = None,
            agent_name: str | None = None,
            pre_result: str | None = None,
            previous_agent_result: str | None = None,
            storage: StorageAdapter | None = None,
            old_memory: List[dict] | None = None,
            conversation_id: str | None = None,
            **kwargs,
    ) -> List[Any]:
        """Main entry point for execution."""
        logger.debug("[TaskEngine] Starting execution for: %s", input_prompt)

        self.context = {
            "input_prompt": input_prompt,
            "pre_result": pre_result,
            "old_memory": old_memory,
            "conversation_id": conversation_id,
            **(kwargs or {}),
        }
        self.results = []
        self.last_result = None
        self.n_steps = 0

        self._validate_instructions_type()

        return await self._execute(task_agent_input=previous_agent_result, pre_result=pre_result)