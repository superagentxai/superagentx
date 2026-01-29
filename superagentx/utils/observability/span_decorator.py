import functools
import logging
import json
import os
import time
from typing import Any

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

logger = logging.getLogger(__name__)
MAX_ATTR_LEN = 2048  # safe default for OTEL + DB


OTEL_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
otel_tracer = trace.get_tracer("superagentx.agent")

def _safe_serialize(value: Any) -> str | int | float | bool | None:
    """
    Convert value into a span-safe primitive.
    """
    if value is None:
        return None

    if isinstance(value, (str, int, float, bool)):
        return value

    try:
        return json.dumps(value, default=str)
    except Exception:
        return str(value)

def _truncate(value: Any, limit: int = MAX_ATTR_LEN):
    if isinstance(value, str) and len(value) > limit:
        return value[:limit] + "...(truncated)"
    return value


def agent_span(func):
    """
    Agent span decorator.

    Priority:
    1. OpenTelemetry span (if OTEL endpoint configured)
    2. SQL span (StorageAdapter)
    3. No-op
    """

    async def add_result_to_span_attributes(
            *,
            storage=None,
            span_id: str | None,
            result: Any,
            prefix: str = "result",
    ):
        """
        Safely add result object fields to span attributes.

        - storage: StorageAdapter or None
        - span_id: span identifier
        - result: GoalResult | dict | pydantic | Any
        """

        if not storage or not span_id or not result:
            return

        try:
            # Convert pydantic model → dict
            if hasattr(result, "model_dump"):
                data = result.model_dump(exclude_none=True)
            elif isinstance(result, dict):
                data = result
            else:
                # Fallback: store whole object as string
                await storage.add_span_attribute(
                    span_id=span_id,
                    key=f"{prefix}.value",
                    value=_truncate(_safe_serialize(result)),
                )
                return

            for key, value in data.items():
                try:
                    attr_key = f"{prefix}.{key}"
                    safe_value = _truncate(_safe_serialize(value))

                    await storage.add_span_attribute(
                        span_id=span_id,
                        key=attr_key,
                        value=safe_value,
                    )
                except Exception as attr_err:
                    logger.debug(
                        f"Span attribute skipped: {key} ({attr_err})",
                        extra={"span_id": span_id},
                    )

        except Exception as e:
            logger.debug(
                f"add_result_to_span_attributes failed (non-blocking): {e}",
                extra={"span_id": span_id},
            )

    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        pipe_id = kwargs.get("pipe_id")
        conversation_id = kwargs.get("conversation_id")
        storage = kwargs.get("storage")

        span_name = f"agent.execute::{self.name}"
        span_id = f"{pipe_id}:{self.agent_id}" if pipe_id else None
        start_time = time.perf_counter()

        # -------------------------------------------------
        # CASE 1: OpenTelemetry
        # -------------------------------------------------
        if OTEL_ENDPOINT and pipe_id:
            with otel_tracer.start_as_current_span(
                name=span_name,
                attributes={
                    "pipe.id": pipe_id,
                    "agent.id": self.agent_id,
                    "agent.name": self.name,
                    "conversation.id": conversation_id or pipe_id,
                },
            ) as span:
                try:
                    result = await func(self, *args, **kwargs)

                    span.add_event(
                        "agent.completed",
                        {"goal_satisfied": getattr(result, "is_goal_satisfied", None)},
                    )
                    span.set_status(Status(StatusCode.OK))
                    return result

                except Exception as e:
                    span.record_exception(e)
                    span.add_event("agent.error", {"error": str(e)})
                    span.set_status(
                        Status(StatusCode.ERROR, description=str(e))
                    )
                    raise

        # -------------------------------------------------
        # CASE 2: SQL Storage
        # -------------------------------------------------
        if storage and pipe_id:
            try:
                await storage.start_span(
                    span_id=span_id,
                    trace_id=pipe_id,
                    span_name=span_name,
                    span_kind="agent",
                    status="started",
                )

                await storage.add_span_attribute(
                    span_id=span_id,
                    key="conversation_id",
                    value=conversation_id or pipe_id,
                )

                await storage.add_span_event(
                    span_id=span_id,
                    event_name="agent.start",
                    event_data={"agent_name": self.name},
                )

                result = await func(self, *args, **kwargs)
                await add_result_to_span_attributes(
                    storage=storage,
                    span_id=span_id,
                    result=result,
                )

                await storage.add_span_event(
                    span_id=span_id,
                    event_name="agent.completed",
                    event_data={
                        "goal_satisfied": getattr(result, "is_goal_satisfied", None)
                    },
                )

                duration_ms = int((time.perf_counter() - start_time) * 1000)

                await storage.add_span_attribute(
                    span_id=span_id,
                    key="duration_ms",
                    value=duration_ms,
                )

                await storage.end_span(
                    span_id=span_id,
                    status="ok",
                )

                return result

            except Exception as e:
                await storage.add_span_event(
                    span_id=span_id,
                    event_name="agent.error",
                    event_data={"error": str(e)},
                )

                await storage.end_span(
                    span_id=span_id,
                    status="error",
                    error_message=str(e),
                )
                raise

        # -------------------------------------------------
        # CASE 3: No observability
        # -------------------------------------------------
        return await func(self, *args, **kwargs)

    return wrapper
