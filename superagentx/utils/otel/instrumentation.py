import os
import time
import json
import psutil
from typing import Any
from functools import wraps

from pydantic import BaseModel

from opentelemetry import trace, metrics
from opentelemetry.trace import get_current_span
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader, ConsoleMetricExporter

from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

# --- Config ---
METRICS_ENABLED = True
OTEL_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")  # Example: http://localhost:4317
SERVICE = os.getenv("OTEL_SERVICE_NAME", "superagentx")

# --- Resource Info ---
resource = Resource(attributes={SERVICE_NAME: SERVICE})

# --- Tracing Setup ---
if METRICS_ENABLED:
    trace_provider = TracerProvider(resource=resource)

    if OTEL_ENDPOINT:
        span_exporter = OTLPSpanExporter(endpoint=OTEL_ENDPOINT, insecure=True)
    else:
        span_exporter = ConsoleSpanExporter()

    trace_provider.add_span_processor(BatchSpanProcessor(span_exporter))
    trace.set_tracer_provider(trace_provider)

tracer = trace.get_tracer(__name__)

# --- Metrics Setup ---
if METRICS_ENABLED:
    if OTEL_ENDPOINT:
        metric_exporter = OTLPMetricExporter(endpoint=OTEL_ENDPOINT, insecure=True)
    else:
        metric_exporter = ConsoleMetricExporter()

    metric_reader = PeriodicExportingMetricReader(metric_exporter)
    metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[metric_reader]))
    meter = metrics.get_meter(__name__)

    function_duration = meter.create_histogram("function_duration_ms", unit="ms")
    function_calls = meter.create_counter("function_calls_total")
else:
    function_duration = None
    function_calls = None


# --- Utility: Set Span Attributes ---
async def set_span_attributes(data: BaseModel | dict | list, prefix: str = ""):
    if not METRICS_ENABLED:
        return

    span = get_current_span()
    if not span.is_recording():
        return

    def _set_attribute(key: str, value: Any):
        if isinstance(value, (str, int, float, bool)):
            span.set_attribute(key, value)
        else:
            try:
                span.set_attribute(key, json.dumps(value))
            except Exception:
                span.set_attribute(key, str(value))

    if isinstance(data, BaseModel):
        data = data.model_dump(exclude_none=True)

    if isinstance(data, dict):
        for k, v in data.items():
            attr_key = f"{prefix}{k}"
            _set_attribute(attr_key, v)

    elif isinstance(data, list):
        for idx, item in enumerate(data):
            if isinstance(item, BaseModel):
                item = item.model_dump(exclude_none=True)
            if isinstance(item, dict):
                for k, v in item.items():
                    attr_key = f"{prefix}{idx}.{k}"
                    _set_attribute(attr_key, v)
            else:
                _set_attribute(f"{prefix}{idx}", item)


# --- Decorator: Trace + Metrics + Memory ---
def otel_metrics_traced_async(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        if not METRICS_ENABLED:
            return await func(*args, **kwargs)

        start_time = time.perf_counter()
        if function_calls:
            function_calls.add(1, {"function.name": func.__name__})

        try:
            arg_data = json.dumps({"args": args, "kwargs": kwargs}, default=str)
        except Exception:
            arg_data = str((args, kwargs))

        with tracer.start_as_current_span(func.__name__) as span:
            span.set_attribute("function.name", func.__name__)
            span.set_attribute("args", arg_data)

            result = None
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration_ms = (time.perf_counter() - start_time) * 1000
                if function_duration:
                    function_duration.record(duration_ms, {"function.name": func.__name__})

                try:
                    result_data = json.dumps(result, default=str)
                except Exception:
                    result_data = str(result)

                span.set_attribute("return_value", result_data)
                span.set_attribute("duration_ms", round(duration_ms, 2))

                # Memory info
                proc = psutil.Process()
                mem_info = proc.memory_info()
                span.set_attribute("memory.rss_mb", round(mem_info.rss / (1024 * 1024), 2))
                span.set_attribute("memory.percent", psutil.virtual_memory().percent)

    return wrapper
