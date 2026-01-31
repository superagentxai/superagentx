import functools
import logging
import os
import time

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from superagentx.utils.observability.metrics import record_metric_safe

logger = logging.getLogger(__name__)

OTEL_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
otel_tracer = trace.get_tracer("superagentx.pipe")


def pipe_trace(func):
    """
    Trace decorator for AgentXPipe.flow

    Priority:
    1. OTEL exporter (if endpoint configured)
    2. SQL storage (workflow_store=True)
    3. No-op
    """


    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        # query_instruction = args[0] if args else None
        query_instruction = kwargs.get("query_instruction")
        conversation_id = kwargs.get("conversation_id")

        # -------------------------------------------------
        # CASE 1: OpenTelemetry
        # -------------------------------------------------
        if OTEL_ENDPOINT:
            with otel_tracer.start_as_current_span(
                name="AgentXPipe.flow",
                attributes={
                    "pipe.id": self.pipe_id,
                    "pipe.name": self.name,
                    "conversation.id": conversation_id or None,
                    "query": query_instruction,
                },
            ) as span:
                try:
                    result = await func(self, *args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(
                        Status(StatusCode.ERROR, description=str(e))
                    )
                    raise

        # -------------------------------------------------
        # CASE 2: SQL Storage (workflow_store)
        # -------------------------------------------------
        if self.workflow_store:
            try:
                self.storage = await self._load_storage_once()

                await self.storage.start_trace(
                    trace_id=self.pipe_id,
                    conversation_id=conversation_id or None,
                    query_input=query_instruction,
                    status="started",
                    metadata={},
                )
                start = time.perf_counter()
                try:
                    result = await func(self, *args, **kwargs)
                    await record_metric_safe(
                        storage=self.storage,
                        name="pipe.success_total",
                        value=1,
                        trace_id=self.pipe_id,
                    )
                    return result
                finally:
                    duration = (time.perf_counter() - start) * 1000
                    await record_metric_safe(
                        storage=self.storage,
                        name="pipe.duration_ms",
                        value=duration,
                        trace_id=self.pipe_id,
                    )
            except Exception as e:
                try:
                    await self.storage.end_trace(
                        trace_id=self.pipe_id,
                        status="error",
                        error_message=str(e),
                    )
                except Exception as trace_err:
                    logger.debug(
                        f"Trace end failed (non-blocking): {trace_err}",
                        extra={"pipe_id": self.pipe_id},
                    )
                raise

            finally:
                try:
                    await self.storage.close()
                except Exception:
                    pass

        # -------------------------------------------------
        # CASE 3: No observability
        # -------------------------------------------------
        return await func(self, *args, **kwargs)

    return wrapper

