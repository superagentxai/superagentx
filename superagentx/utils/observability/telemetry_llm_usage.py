import logging
from typing import Any

from superagentx.db_store import StorageAdapter

logger = logging.getLogger(__name__)


async def extract_llm_usage(storage: StorageAdapter, span_id: str,  llm_response: Any, ):
    """
    Safely extract LLM usage from response.

    Supports:
    - list[Message]
    - single Message
    - partial token fields

    Never raises.
    """
    usage = {
        "model": None,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "reasoning_tokens": 0,
        "total_tokens": 0,
        "message_count": 0,
    }

    try:
        # Normalize to list
        messages = llm_response
        if not isinstance(messages, (list, tuple)):
            messages = [messages]

        for msg in messages:
            if not msg:
                continue

            usage["message_count"] += 1

            # Model (take first non-null)
            model = getattr(msg, "model", None)
            if model and not usage["model"]:
                usage["model"] = model

            # Token fields (OpenAI-style)
            usage["prompt_tokens"] += int(
                getattr(msg, "prompt_tokens", 0) or 0
            )
            usage["completion_tokens"] += int(
                getattr(msg, "completion_tokens", 0) or 0
            )
            usage["reasoning_tokens"] += int(
                getattr(msg, "reasoning_tokens", 0) or 0
            )
            usage["total_tokens"] += int(
                getattr(msg, "total_tokens", 0) or 0
            )

        """
            Attach LLM usage to the current engine span.
        """
        if storage and span_id:

            for key, value in usage.items():
                if value is None:
                    continue

                await storage.add_span_attribute(
                    span_id=span_id,
                    key=f"llm.{key}",
                    value=value,
                )

    except Exception as e:
        logger.debug(f"LLM usage extraction failed (non-blocking): {e}")
