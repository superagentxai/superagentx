import logging
from typing import Any

from sqlalchemy import  select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
)

from superagentx.db_store.schema.models import (
    Base, DBPipe, DBAgent, DBTrace, DBSpan,
    DBSpanAttribute, DBSpanEvent, DBMetric
)

from superagentx.db_store.db_interface import StorageAdapter
from superagentx.db_store.sql_status_enum import PipeStatus
from superagentx.utils.helper import utcnow, ensure_utc, duration_ms

logger = logging.getLogger(__name__)


class SQLBaseStorage(StorageAdapter):
    def __init__(self, connection_string: str):
        self.engine = create_async_engine(
            connection_string,
            pool_pre_ping=True,
            future=True,
        )
        self.session_factory = async_sessionmaker(
            self.engine,
            expire_on_commit=False,
        )

    async def setup(self) -> None:
        async with self.engine.connect() as conn:
            await conn.run_sync(Base.metadata.create_all)

    # -------------------------------------------------------------------
    # Pipe Operations
    # -------------------------------------------------------------------

    async def pipe_exists(self, pipe_id: str) -> bool:
        async with self.session_factory() as session:
            stmt = select(1).where(DBPipe.pipe_id == pipe_id)
            return (await session.execute(stmt)).scalar() is not None

    async def create_pipe(
            self,
            pipe_id: str,
            conversation_id: str = None,
            input_query: str = None ,
            executed_by: str = "System",
    ) -> None:
        async with self.session_factory() as session:
            try:
                async with session.begin():
                    session.add(
                        DBPipe(
                            pipe_id=pipe_id,
                            executed_by=executed_by,
                            status="Pending",
                        )
                    )

                async with session.begin():
                    session.add(
                        DBTrace(
                            trace_id=pipe_id,  # pipe_id == trace_id
                            conversation_id=conversation_id or pipe_id,
                            query_input=input_query,
                            status="started",
                            start_time=utcnow(),
                        )
                    )

            except IntegrityError:
                logger.debug(
                    "Pipe already exists",
                    extra={"pipe_id": pipe_id},
                )

    async def update_pipe_status(
            self,
            pipe_id: str,
            status: PipeStatus,
            error: str | None = None,
    ) -> None:
        async with self.session_factory() as session:
            async with session.begin():
                pipe = await session.scalar(
                    select(DBPipe).where(DBPipe.pipe_id == pipe_id)
                )

                if not pipe:
                    logger.debug(
                        "Pipe not found",
                        extra={"pipe_id": pipe_id},
                    )
                    return

                pipe.status = status
                pipe.error_details = error

                # 🔚 End trace when pipe reaches terminal state
                if status in {"Completed", "Failed"}:
                    trace = await session.scalar(
                        select(DBTrace).where(DBTrace.trace_id == pipe_id)
                    )

                    if trace and not trace.end_time:
                        trace.end_time = utcnow()

                        start = ensure_utc(trace.start_time)
                        end = ensure_utc(trace.end_time)

                        trace.duration_ms = int(
                            (end - start).total_seconds() * 1000
                        )

                        trace.status = (
                            "success" if status == "Completed" else "error"
                        )
                        trace.error_message = error

    # -------------------------------------------------------------------
    # Agent Operations
    # -------------------------------------------------------------------

    async def is_agent_processed(
            self,
            pipe_id: str,
            agent_id: str,
            agent_name: str
    ) -> bool:
        async with self.session_factory() as session:
            stmt = select(1).where(
                DBAgent.pipe_id == pipe_id,
                DBAgent.agent_name == agent_name,
            )
            return (await session.execute(stmt)).scalar() is not None

    async def mark_agent_completed(
            self,
            pipe_id: str,
            agent_id: str,
            agent_name: str,
            input_content: str,
            status: PipeStatus,
            goal_result: Any = None,
            updated_by: str = "System",
    ) -> None:
        async with self.session_factory() as session:
            try:
                async with session.begin():

                    # --- Serialize goal_result safely ---
                    if goal_result is None:
                        result_data: dict | None = None
                    elif hasattr(goal_result, "model_dump"):
                        try:
                            result_data = goal_result.model_dump(
                                mode="json",
                                exclude_none=True,
                                round_trip=True,
                            )
                        except Exception as ex:
                            logger.warning(
                                f"goal_result serialization failed {ex}",
                                extra={
                                    "pipe_id": pipe_id,
                                    "agent_id": agent_id,
                                },
                            )
                            result_data = None
                    else:
                        result_data = goal_result

                    agent = await session.scalar(
                        select(DBAgent).where(
                            DBAgent.pipe_id == pipe_id,
                            DBAgent.agent_name == agent_name,
                        )
                    )

                    if agent:
                        agent.status = status
                        agent.result_data = result_data
                        agent.updated_by = updated_by
                    else:
                        session.add(
                            DBAgent(
                                pipe_id=pipe_id,
                                agent_id=agent_id,
                                agent_name=agent_name,
                                input_content=input_content,
                                status=status,
                                result_data=result_data,
                                updated_by=updated_by,
                            )
                        )

                    logger.debug(
                        "Agent completion recorded",
                        extra={
                            "pipe_id": pipe_id,
                            "agent_id": agent_id,
                            "agent_name": agent_name,
                            "status": status,
                        },
                    )

            except IntegrityError:
                logger.warning(
                    "Duplicate agent execution blocked",
                    extra={
                        "pipe_id": pipe_id,
                        "agent_id": agent_id,
                        "agent_name": agent_name,
                    },
                )
            except SQLAlchemyError:
                logger.exception(
                    "Database error while marking agent completed",
                    extra={
                        "pipe_id": pipe_id,
                        "agent_id": agent_id,
                        "agent_name": agent_name,
                    },
                )
                raise
            except Exception:
                logger.exception(
                    "Unexpected error while marking agent completed",
                    extra={
                        "pipe_id": pipe_id,
                        "agent_id": agent_id,
                        "agent_name": agent_name,
                    },
                )
                raise

    async def start_trace(
        self,
        trace_id: str,
        conversation_id: str,
        query_input: str | None = None,
        metadata: dict | None = None,
        status: str = "started",
    ) -> None:
        async with self.session_factory() as session:
            async with session.begin():
                session.add(
                    DBTrace(
                        trace_id=trace_id,
                        conversation_id=conversation_id,
                        query_input=query_input,
                        status=status,
                        metadata_=metadata,
                        start_time=utcnow(),
                    )
                )

    async def end_trace(
            self,
            trace_id: str,  # pipe_id
            status: str = "success",
            error_message: str | None = None,
    ) -> None:
        async with self.session_factory() as session:
            async with session.begin():
                trace = await session.scalar(
                    select(DBTrace).where(DBTrace.trace_id == trace_id)
                )
                if not trace:
                    logger.debug(
                        "end_trace skipped: trace not found",
                        extra={"trace_id": trace_id},
                    )
                    return

                trace.end_time = utcnow()
                trace.duration_ms = duration_ms(trace.start_time, trace.end_time)
                trace.status = status
                trace.error_message = error_message

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
        async with self.session_factory() as session:
            async with session.begin():
                trace = await session.scalar(
                    select(DBTrace).where(DBTrace.trace_id == trace_id)
                )
                if not trace:
                    logger.debug(
                        "start_span skipped: trace not found",
                        extra={"trace_id": trace_id},
                    )
                    return

                session.add(
                    DBSpan(
                        span_id=span_id,
                        trace_id=trace.id,  # FK to trace PK
                        parent_span_id=parent_span_id,  #  hierarchy
                        span_name=span_name,
                        span_kind=span_kind,
                        status=status,
                        start_time=utcnow(),
                    )
                )

    async def end_span(
            self,
            *,
            span_id: str,
            status: str = "ok",
            error_message: str | None = None,
    ) -> None:
        async with self.session_factory() as session:
            async with session.begin():
                span = await session.scalar(
                    select(DBSpan).where(DBSpan.span_id == span_id)
                )
                if not span:
                    return

                span.end_time = utcnow()
                span.duration_ms = int(
                    (ensure_utc(span.end_time) - ensure_utc(span.start_time))
                    .total_seconds() * 1000
                )
                span.status = status
                span.error_message = error_message

    async def add_span_attribute(
        self,
        span_id: str,
        key: str,
        value: Any,
    ) -> None:
        async with self.session_factory() as session:
            async with session.begin():
                session.add(
                    DBSpanAttribute(
                        span_id=span_id,
                        attribute_key=key,
                        attribute_value=value,
                    )
                )

    async def add_span_attributes(
        self,
        span_id: str,
        attributes: dict[str, Any],
    ) -> None:
        async with self.session_factory() as session:
            async with session.begin():
                for key, value in attributes.items():
                    session.add(
                        DBSpanAttribute(
                            span_id=span_id,
                            attribute_key=key,
                            attribute_value=value,
                        )
                    )

    async def add_span_event(
        self,
        span_id: str,
        event_name: str,
        event_data: dict | None = None,
    ) -> None:
        async with self.session_factory() as session:
            async with session.begin():
                session.add(
                    DBSpanEvent(
                        span_id=span_id,
                        event_name=event_name,
                        event_time=utcnow(),
                        event_data=event_data,
                    )
                )

    async def record_metric(
            self,
            *,
            name: str,
            value: float,
            labels: dict | None = None,
            trace_id: str | None = None,
            span_id: str | None = None,
    ) -> None:
        async with self.session_factory() as session:
            async with session.begin():
                session.add(
                    DBMetric(
                        name=name,
                        value=value,
                        labels=labels,
                        trace_id=trace_id,
                        span_id=span_id,
                    )
                )

    async def close(self) -> None:
        """
        Properly close async engine and release all resources.
        Must be called BEFORE event loop shutdown.
        """
        if self.engine:
            await self.engine.dispose()
            logger.debug("SQLAlchemy async engine disposed")


# -------------------------------------------------------------------
# Storage Implementations
# -------------------------------------------------------------------


class SQLiteStorage(SQLBaseStorage):
    """SQLite async storage (aiosqlite required)."""

    def __init__(self, db_path: str = "agents.db"):
        super().__init__(f"sqlite+aiosqlite:///{db_path}")


class PostgresStorage(SQLBaseStorage):
    """PostgreSQL async storage (asyncpg required)."""

    def __init__(
            self,
            host: str,
            user: str,
            password: str,
            db: str,
            port: int = 5432,
    ):
        super().__init__(
            f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"
        )
