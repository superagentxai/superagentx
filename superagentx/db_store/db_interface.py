from abc import ABC, abstractmethod
from typing import Any


class StorageAdapter(ABC):

    # -------------------------------------------------
    # Lifecycle
    # -------------------------------------------------

    @abstractmethod
    async def setup(self):
        """Initialize connection and create tables/collections."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close connections and release resources."""
        pass

    # -------------------------------------------------
    # Pipe / Trace Operations
    # Trace == Pipe (trace_id = pipe_id)
    # -------------------------------------------------

    @abstractmethod
    async def create_pipe(
        self,
        pipe_id: str,
        conversation_id: str | None = None,
        input_query: str | None = None,
        executed_by: str = "System",
    ):
        pass

    @abstractmethod
    async def update_pipe_status(
        self,
        pipe_id: str,
        status: str,
        error: str | None = None,
    ):
        pass

    @abstractmethod
    async def start_trace(
        self,
        trace_id: str,
        conversation_id: str,
        query_input: str | None = None,
        status: str = "started",
        metadata: dict | None = None,
    ) -> None:
        """
        Start a trace.
        NOTE: In SuperAgentX, trace_id == pipe_id
        """
        pass

    @abstractmethod
    async def end_trace(
        self,
        trace_id: str,
        status: str = "success",
        error_message: str | None = None,
    ) -> None:
        pass

    # -------------------------------------------------
    # Agent Operations
    # -------------------------------------------------

    @abstractmethod
    async def is_agent_processed(
        self,
        pipe_id: str,
        agent_id: str,
        agent_name: str,
    ) -> bool:
        pass

    @abstractmethod
    async def mark_agent_completed(
        self,
        pipe_id: str,
        agent_id: str,
        agent_name: str,
        status: str,
        input_content: str,
        goal_result: Any = None,
        updated_by: str = "System",
    ):
        pass

    # -------------------------------------------------
    # Span Operations (Parent → Child supported)
    # -------------------------------------------------

    @abstractmethod
    async def start_span(
        self,
        *,
        span_id: str,
        trace_id: str,
        span_name: str,
        span_kind: str,
        parent_span_id: str | None = None,
        status: str = "started",
    ) -> None:
        """
        Start a span.

        parent_span_id:
            - None → root span under trace (e.g. Agent span)
            - span_id → child span (engine / tool / llm)
        """
        pass

    @abstractmethod
    async def end_span(
        self,
        *,
        span_id: str,
        status: str = "ok",
        error_message: str | None = None,
    ) -> None:
        pass

    # -------------------------------------------------
    # Span Attributes
    # -------------------------------------------------

    @abstractmethod
    async def add_span_attribute(
        self,
        *,
        span_id: str,
        key: str,
        value: Any,
    ) -> None:
        pass

    # -------------------------------------------------
    # Span Events
    # -------------------------------------------------

    @abstractmethod
    async def add_span_event(
        self,
        *,
        span_id: str,
        event_name: str,
        event_data: dict | None = None,
    ) -> None:
        pass
