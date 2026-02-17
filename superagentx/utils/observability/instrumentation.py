import os
import time
import uuid
import json
import psutil
import logging
from functools import wraps
from typing import Any, Callable

from opentelemetry import trace, metrics
from opentelemetry.trace import get_current_span
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    PeriodicExportingMetricReader,
    ConsoleMetricExporter,
)

from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

from superagentx.db_store.db_interface import StorageAdapter

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# CONFIG
# -------------------------------------------------------------------

OTEL_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
SERVICE = os.getenv("OTEL_SERVICE_NAME", "superagentx")
TENANT_ID = os.getenv("TENANT_ID", "default")

USE_OTEL = bool(OTEL_ENDPOINT)

# -------------------------------------------------------------------
# OTEL INITIALIZATION (ONLY IF ENABLED)
# -------------------------------------------------------------------

tracer = None
meter = None
function_duration = None
function_calls = None

if USE_OTEL:
    resource = Resource(
        attributes={
            SERVICE_NAME: SERVICE,
            "tenant_id": TENANT_ID,
        }
    )

    # ---- Tracing ----
    trace_provider = TracerProvider(resource=resource)
    trace_provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(endpoint=OTEL_ENDPOINT, insecure=True)
        )
    )
    trace.set_tracer_provider(trace_provider)
    tracer = trace.get_tracer(__name__)

    # ---- Metrics ----
    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=OTEL_ENDPOINT, insecure=True)
    )
    metrics.set_meter_provider(
        MeterProvider(resource=resource, metric_readers=[metric_reader])
    )

    meter = metrics.get_meter(__name__)
    function_duration = meter.create_histogram(
        "function_duration_ms", unit="ms"
    )
    function_calls = meter.create_counter(
        "function_calls_total"
    )

# -------------------------------------------------------------------
# INTERNAL HELPERS
# -------------------------------------------------------------------

async def _safe_db_call(coro):
    """Never block execution on observability failures."""
    try:
        await coro
    except Exception as e:
        logger.debug(f"Observability DB call failed (ignored): {e}")


def _serialize(value: Any) -> str:
    try:
        return json.dumps(value, default=str)
    except Exception:
        return str(value)


# -------------------------------------------------------------------
# MAIN DECORATOR
# -------------------------------------------------------------------

def observability_async(
    *,
    storage: StorageAdapter | None,
    pipe_id: str | None,
    span_kind: str = "function",  # agent | engine | tool | llm | human
):
    """
    Unified Observability Decorator

    RULE:
    - If OTEL endpoint exists → publish to OTEL
    - Else → persist via SQLAlchemy
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            span_id = f"{pipe_id}:{func.__name__}:{uuid.uuid4().hex}"
            start_perf = time.perf_counter()
            proc = psutil.Process()

            # ------------------------------------------------
            # SQL SPAN START
            # ------------------------------------------------
            if not USE_OTEL and storage and pipe_id:
                await _safe_db_call(
                    storage.start_span(
                        span_id=span_id,
                        trace_id=pipe_id,
                        span_name=func.__name__,
                        span_kind=span_kind,
                        status="started",
                    )
                )

            try:
                # ------------------------------------------------
                # OTEL SPAN
                # ------------------------------------------------
                if USE_OTEL and tracer:
                    with tracer.start_as_current_span(func.__name__) as otel_span:
                        otel_span.set_attribute("pipe_id", pipe_id or "")
                        otel_span.set_attribute("span.kind", span_kind)
                        return await func(*args, **kwargs)
                else:
                    return await func(*args, **kwargs)

            except Exception as e:
                # ----------------------------
                # SQL EVENT (ERROR)
                # ----------------------------
                if not USE_OTEL and storage:
                    await _safe_db_call(
                        storage.add_span_event(
                            span_id=span_id,
                            event_name="exception",
                            event_data={"error": str(e)},
                        )
                    )
                raise

            finally:
                duration_ms = (time.perf_counter() - start_perf) * 1000
                mem = proc.memory_info()

                metrics_payload = {
                    "duration_ms": round(duration_ms, 2),
                    "memory.rss_mb": round(mem.rss / (1024 * 1024), 2),
                    "memory.percent": psutil.virtual_memory().percent,
                }

                # ------------------------------------------------
                # OTEL METRICS
                # ------------------------------------------------
                if USE_OTEL:
                    span = get_current_span()
                    if span and span.is_recording():
                        for k, v in metrics_payload.items():
                            span.set_attribute(k, v)

                    if function_calls:
                        function_calls.add(1, {"function": func.__name__})

                    if function_duration:
                        function_duration.record(
                            duration_ms,
                            {"function": func.__name__},
                        )

                # ------------------------------------------------
                # SQL ATTRIBUTES + SPAN END
                # ------------------------------------------------
                if not USE_OTEL and storage:
                    for k, v in metrics_payload.items():
                        await _safe_db_call(
                            storage.add_span_attribute(
                                span_id=span_id,
                                key=f"metrics.{k}",
                                value=v,
                            )
                        )

                    await _safe_db_call(
                        storage.end_span(
                            span_id=span_id,
                            status="ok",
                        )
                    )

        return wrapper
    return decorator
