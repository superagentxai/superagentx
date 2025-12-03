import asyncio
import inspect
import logging
import traceback
import re
from typing import Any, Callable, Dict, List, Awaitable

from superagentx.base import BaseEngine
from superagentx.handler.base import BaseHandler

logger = logging.getLogger(__name__)

SAFE_BUILTINS = {
    "len": len,
    "range": range,
    "sum": sum,
    "min": min,
    "max": max,
    "sorted": sorted,
}


def _get_from_path(root: Any, path: str) -> Any:
    """ Traverse nested dict/list using dotted + indexed path. (Synchronous utility)"""
    if root is None:
        return None

    cur = root
    # Split by dot, but not if the dot is inside square brackets (e.g., in a path like 'a.[b.c][0].d')
    # The original regex `r"\.(?![^\[]*\])"` is a common way to split by dot outside brackets.
    parts = re.split(r"\.(?![^\[]*])", path) if path else []

    for part in parts:
        # Find the key part before any index brackets
        m = re.match(r"^([^\[\]]+)", part)
        key = m.group(1) if m else part

        try:
            if isinstance(cur, dict):
                # Using .get for dicts to avoid KeyError
                cur = cur.get(key)
            else:
                # Using getattr for objects to avoid AttributeError
                cur = getattr(cur, key, None)
        except Exception:
            # Catching errors during attribute/key access
            return None

        if cur is None:
            return None

        # Resolve list/tuple indices
        idxs = re.findall(r"\[(\d+)]", part)
        for idx in idxs:
            try:
                # Type must support indexing (list, tuple, dict, etc.)
                cur = cur[int(idx)]
            except Exception:
                return None

    return cur


async def _safe_exec(code: str) -> Dict[str, Any]:
    """
    Executes code safely in a separate thread using a limited builtins set.
    """

    def _exec_block() -> Dict[str, Any]:
        local_ns: Dict[str, Any] = {}
        try:
            # Use exec with limited builtins
            exec(code, {"__builtins__": SAFE_BUILTINS}, local_ns)
            return {"locals": local_ns}
        except Exception as e:
            # Capture execution errors
            return {"error": str(e), "traceback": traceback.format_exc()}

    # Run the potentially blocking synchronous exec in a separate thread
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

        self._validate_instructions_type()  # Synchronous validation

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
    _prev_re = re.compile(r"\$prev(?:\.([A-Za-z0-9_.\[\]]+))?")

    def _resolve_prev_reference(self, value: str) -> Any:
        if not self.last_result:
            return None

        # Find $prev or $prev.xxx inside any string
        m = self._prev_re.search(value)
        if not m:
            return None

        path = m.group(1)  # path part (e.g., 'key' or 'key.list[0]')

        wrapper = self.last_result

        # Determine inner root (parallel_map, successes, failures, result, etc.)
        if "parallel_map" in wrapper:
            inner = wrapper["parallel_map"]

        elif "successes" in wrapper or "failures" in wrapper:
            # Result from a parallel run
            inner = wrapper

        else:
            # Result from a single method call: {"method_name": {"success":..., "result":...}}
            try:
                first_val = next(iter(wrapper.values()))
                if isinstance(first_val, dict):
                    # Prioritize 'result' or 'data' for method outputs
                    if "result" in first_val:
                        inner = first_val["result"]
                    elif "data" in first_val:
                        inner = first_val["data"]
                    else:
                        inner = first_val  # Fallback to the method-specific dictionary
                else:
                    inner = first_val  # The result itself if it wasn't wrapped in a dict
            except StopIteration:
                return None

        # If user requested just "$prev"
        if not path:
            return inner

        # Resolve nested path
        return _get_from_path(inner, path)

    def _resolve_dynamic_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve $prev references recursively, including inside strings. (Synchronous utility)"""

        prev_pattern = re.compile(r"\$prev(?:\.([A-Za-z0-9_.\[\]]+))?")

        # logger.info(f"Prev Function {params} {prev_pattern}") # Log removed for cleaner code

        def _resolve_string(val: str) -> str | Any:
            # Entire string is exactly a $prev expression (e.g., '$prev.data.value')
            if prev_pattern.fullmatch(val):
                resolved = self._resolve_prev_reference(val)
                # If the entire string is $prev, return the resolved object, not its string representation
                return resolved

            # Inline substitution (e.g., 'The result is: $prev.result')
            def repl(match):
                full = match.group(0)
                resolved = self._resolve_prev_reference(full)
                # For inline, we must return a string
                return str(resolved) if resolved is not None else full

            return prev_pattern.sub(repl, val)

        def _resolve(v: Any) -> Any:
            if isinstance(v, str):
                return _resolve_string(v)
            if isinstance(v, dict):
                return {k: _resolve(sub) for k, sub in v.items()}
            if isinstance(v, list):
                return [_resolve(item) for item in v]
            return v

        # Recursively resolve all parameters
        return {k: _resolve(v) for k, v in params.items()}

    # ----------------------------------------------------
    # Method Execution
    # ----------------------------------------------------
    async def _execute_method(self, method_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single handler or tool method."""
        self._ensure_step_limit()
        self.n_steps += 1

        func = self.tools.get(method_name) or getattr(self.handler, method_name, None)

        if func is None:
            result = {method_name: {"success": False, "error": f"Method `{method_name}` not found"}}
            self.last_result = result
            return result

        # Resolve dynamic parameters before execution
        params = self._resolve_dynamic_params(params or {})

        try:
            if inspect.iscoroutinefunction(func):
                # Function is natively async, await it directly
                output = await func(**params)
            else:
                # Function is synchronous, run it in a separate thread
                output = await asyncio.to_thread(func, **params)

            result = {method_name: {"success": True, "result": output}}

        except Exception as e:
            # Capture execution errors
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
    async def _run_parallel(self, parallel_steps: List[Dict[str, Any]]) -> None:
        """Run multiple steps concurrently using asyncio.gather."""
        tasks = []
        method_names = []

        # Prepare tasks (resolving parameters will happen inside _execute_method right before execution)
        for step in parallel_steps:
            if not isinstance(step, dict) or len(step) != 1:
                raise ValueError(f"Invalid parallel step: {step}")
            name, params = next(iter(step.items()))
            method_names.append(name)
            tasks.append(self._execute_method(name, params))

        # Run all tasks concurrently
        batch = await asyncio.gather(*tasks)

        # Process results
        parallel_map = {}
        successes = {}
        failures = {}

        for i, method_name in enumerate(method_names):
            # Each item in batch is the result dict from _execute_method
            step_result = batch[i][method_name]
            if step_result["success"]:
                result_val = step_result["result"]
                parallel_map[method_name] = result_val
                successes[method_name] = result_val
            else:
                parallel_map[method_name] = None
                failures[method_name] = step_result["error"]

        # Final wrapper structure for parallel results
        wrapper = {
            "parallel_results": batch,
            "parallel_map": parallel_map,
            "successes": successes,
            "failures": failures
        }

        self.results.append(wrapper)
        self.last_result = wrapper

        # Increment step count only once for the whole parallel block
        self.n_steps += 1
        self._ensure_step_limit()

    # ----------------------------------------------------
    # Sequential Execution
    # ----------------------------------------------------
    async def _run_sequence(self, steps: List[Dict[str, Any]]) -> None:
        """Run steps one after another."""
        for step in steps:
            if not isinstance(step, dict) or len(step) != 1:
                raise ValueError(f"Invalid sequence step: {step}")
            name, params = next(iter(step.items()))
            # Await each sequential step
            await self._execute_method(name, params)

    # ----------------------------------------------------
    # Main Execution
    # ----------------------------------------------------
    async def _execute(self) -> List[Dict[str, Any]]:
        """Core execution loop for code and instructions."""
        if self.code:
            # Code Execution Step
            if self.safe_mode:
                code_output = await _safe_exec(self.code)
            else:
                # Unsafe mode: exec directly, but still wrap in to_thread since exec is blocking
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

        # Instruction Steps
        for step in self.instructions:
            if isinstance(step, list):
                # Parallel execution
                await self._run_parallel(step)
            elif isinstance(step, dict):
                # Sequential execution (a single method call)
                await self._run_sequence([step])
            else:
                raise ValueError(f"Invalid instruction step: {step}")

        return self.results

    # ----------------------------------------------------
    # Public API
    # ----------------------------------------------------
    async def start(
            self,
            input_prompt: str | None = None,
            pre_result: str | None = None,
            old_memory: List[dict] | None = None,
            conversation_id: str | None = None,
            **kwargs,
    ) -> List[Any]:
        """Main entry point for execution."""
        logger.debug("[TaskEngine] Starting execution for: %s", input_prompt)

        # Set up execution context
        self.context = {
            "input_prompt": input_prompt,
            "pre_result": pre_result,
            "old_memory": old_memory,
            "conversation_id": conversation_id,
            **(kwargs or {}),
        }

        # Reset runtime state
        self.results = []
        self.last_result = None
        self.n_steps = 0

        self._validate_instructions_type()

        # Begin execution and await the result
        return await self._execute()
