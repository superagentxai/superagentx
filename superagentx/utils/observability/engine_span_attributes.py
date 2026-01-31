import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

ENGINE_ATTR_MAX_LEN = 2048  # safe for OTEL + SQL storage



def _engine_safe_serialize(value: Any) -> str | int | float | bool | None:
    """
    Convert any value into a span-safe primitive.
    """
    if value is None:
        return None

    if isinstance(value, (str, int, float, bool)):
        return value

    try:
        return json.dumps(value, default=str)
    except Exception:
        return str(value)


def _engine_truncate(value: Any, limit: int = ENGINE_ATTR_MAX_LEN):
    """
    Prevent huge payloads from breaking telemetry.
    """
    if isinstance(value, str) and len(value) > limit:
        return value[:limit] + "...(truncated)"
    return value


async def add_engine_span_attributes(
    *,
    storage,
    span_id: str | None,
    engine_name: str,
    engine_type: str,  # engine | tool | browser | llm
    input_data: Any | None = None,
    output_data: Any | None = None,
    status: str | None = None,
    error: str | None = None,
    metadata: dict[str, Any] | None = None,
):
    """
    Attach engine-level attributes to a span.

    - Safe: never raises
    - Generic: works for Engine / Tool / Browser / LLM
    - Storage-backed (SQL) or OTEL-compatible

    storage   : StorageAdapter
    span_id   : span identifier
    """

    if not storage or not span_id:
        return

    try:

        await storage.add_span_attribute(
            span_id=span_id,
            key="tool.name",
            value=engine_name,
        )

        await storage.add_span_attribute(
            span_id=span_id,
            key="tool.type",
            value=engine_type,
        )

        if input_data is not None:
            await storage.add_span_attribute(
                span_id=span_id,
                key="tool.input",
                value=_engine_truncate(
                    _engine_safe_serialize(input_data)
                ),
            )

        if output_data is not None:
            print(f"result: {_engine_truncate(
                    _engine_safe_serialize(output_data)
                )} - {span_id}")

            await storage.add_span_attribute(
                span_id=span_id,
                key="tool.output",
                value=_engine_truncate(
                    _engine_safe_serialize(output_data)
                ),
            )

        if status:
            await storage.add_span_attribute(
                span_id=span_id,
                key="tool.status",
                value=status,
            )

        if error:
            await storage.add_span_attribute(
                span_id=span_id,
                key="tool.error",
                value=_engine_truncate(error),
            )

        if metadata:
            for k, v in metadata.items():
                try:
                    await storage.add_span_attribute(
                        span_id=span_id,
                        key=f"tool.meta.{k}",
                        value=_engine_truncate(
                            _engine_safe_serialize(v)
                        ),
                    )
                except Exception as meta_err:
                    logger.debug(
                        f"Engine meta skipped: {k} ({meta_err})",
                        extra={"span_id": span_id},
                    )

    except Exception as e:
        # Telemetry must NEVER break execution
        logger.debug(
            f"add_engine_span_attributes failed (non-blocking): {e}",
            extra={"span_id": span_id},
        )
