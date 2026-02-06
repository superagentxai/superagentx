from opentelemetry import metrics
import os

_meter = metrics.get_meter("superagentx")

PIPE_DURATION = _meter.create_histogram("pipe.duration_ms")
PIPE_SUCCESS = _meter.create_counter("pipe.success_total")
PIPE_FAILURE = _meter.create_counter("pipe.failure_total")

AGENT_DURATION = _meter.create_histogram("agent.duration_ms")
LLM_TOKENS = _meter.create_counter("llm.tokens_total")


OTEL_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")

async def record_metric_safe(
    *,
    storage,
    name: str,
    value: float,
    labels: dict | None = None,
    trace_id: str | None = None,
    span_id: str | None = None,
):
    """
    Record metric to OTEL if available, else SQL.
    Never raises.
    """
    try:
        if OTEL_ENDPOINT:
            # Map name → OTEL instruments
            if name == "pipe.duration_ms":
                PIPE_DURATION.record(value, labels)
            elif name == "pipe.success_total":
                PIPE_SUCCESS.add(value, labels)
            elif name == "pipe.failure_total":
                PIPE_FAILURE.add(value, labels)
            elif name == "agent.duration_ms":
                AGENT_DURATION.record(value, labels)
            elif name.startswith("llm."):
                LLM_TOKENS.add(value, labels)
            return

        # SQL fallback
        if storage:
            await storage.record_metric(
                name=name,
                value=value,
                labels=labels,
                trace_id=trace_id,
                span_id=span_id,
            )

    except Exception:
        # Metrics must NEVER break execution
        pass
