import functools
import logging
from typing import Any, Callable, Coroutine

from superagentx.db_store import StorageAdapter

logger = logging.getLogger(__name__)


def engine_telemetry(
    *,
    engine_type: str,  # engine | tool | browser | llm
    engine_name_resolver: Callable[..., str] | None = None,
):
    """
    Async decorator to attach engine span attributes.

    Requirements:
    - wrapped function must receive:
        storage (StorageAdapter | None)
        pipe_id (str | None)
        agent_id (str | None)

    Span ID format:
        {pipe_id}:{agent_id}:{engine_name}
    """

    def decorator(func: Callable[..., Coroutine[Any, Any, Any]]):

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            storage: StorageAdapter = kwargs.get("storage")
            pipe_id: str = kwargs.get("pipe_id")
            agent_id: str = kwargs.get("agent_id")

            engine_name = (
                engine_name_resolver(*args, **kwargs)
                if engine_name_resolver
                else func.__qualname__
            )

            span_id = None
            if pipe_id and agent_id:
                span_id = f"{pipe_id}:{agent_id}"

            result = None
            error: str | None = None
            status = "ok"

            try:
                result = await func(*args, **kwargs)

                return result

            except Exception as e:
                status = "error"
                error = str(e)
                raise

            finally:
                try:
                    if storage and span_id:
                        from superagentx.utils.observability.engine_span_attributes import (
                            add_engine_span_attributes,
                        )
                        await add_engine_span_attributes(
                            storage=storage,
                            span_id=span_id,
                            engine_name=engine_name,
                            engine_type=engine_type,
                            input_data={
                                "args": args,
                                "kwargs": kwargs,
                            },
                            output_data=result,
                            status=status,
                            error=error,
                        )
                except Exception as tel_err:
                    logger.debug(
                        f"engine_telemetry decorator failed (ignored): {tel_err}",
                        extra={"span_id": span_id},
                    )

        return wrapper

    return decorator
