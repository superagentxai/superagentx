import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    DateTime,
    ForeignKey,
    JSON,
    String,
    Text,
    select,
    UniqueConstraint,
)
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)
from sqlalchemy.sql.sqltypes import BigInteger

from superagentx.db_store.db_interface import StorageAdapter
from superagentx.db_store.sql_status_enum import PipeStatus, AgentStatus

logger = logging.getLogger(__name__)


from datetime import timezone

def ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def duration_ms(start: datetime, end: datetime) -> int:
    start = ensure_utc(start)
    end = ensure_utc(end)
    return int((end - start).total_seconds() * 1000)

def utcnow() -> datetime:
    """Return timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class DBPipe(Base):
    __tablename__ = "pipes"

    id: Mapped[int] = mapped_column(primary_key=True)
    pipe_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    status: Mapped[str] = mapped_column(
        String(30),
        default=PipeStatus.PENDING,
        index=True,
    )
    error_details: Mapped[str | None] = mapped_column(Text)
    executed_by: Mapped[str | None] = mapped_column(String(100))

    updated_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
    )

    agents = relationship(
        "DBAgent",
        back_populates="pipe",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class DBAgent(Base):
    __tablename__ = "agents"
    __table_args__ = (
        UniqueConstraint("pipe_id", "agent_id", name="uq_pipe_agent"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    pipe_id: Mapped[str] = mapped_column(
        ForeignKey("pipes.pipe_id", ondelete="CASCADE"),
        index=True,
    )

    agent_id: Mapped[str] = mapped_column(String(50), index=True)
    agent_name: Mapped[str | None] = mapped_column(String(50))
    input_content: Mapped[str | None] = mapped_column(Text)

    result_data: Mapped[dict | None] = mapped_column(JSON)

    status: Mapped[str] = mapped_column(
        String(30),
        default=AgentStatus.PENDING,
        index=True,
    )

    updated_by: Mapped[str | None] = mapped_column(String(50))

    updated_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
    )

    pipe = relationship("DBPipe", back_populates="agents")

class DBTrace(Base):
    __tablename__ = "otel_traces"

    id: Mapped[int] = mapped_column(primary_key=True)

    trace_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)

    conversation_id: Mapped[str | None] = mapped_column(String(50))

    query_input: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), index=True)
    error_message: Mapped[str | None] = mapped_column(Text)

    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
    )
    end_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    duration_ms: Mapped[int | None] = mapped_column(BigInteger)
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata",
        JSON,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
    )

    spans = relationship(
        "DBSpan",
        back_populates="trace",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

class DBSpan(Base):
    __tablename__ = "otel_spans"

    id: Mapped[int] = mapped_column(primary_key=True)

    span_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)

    trace_id: Mapped[int] = mapped_column(
        ForeignKey("otel_traces.id", ondelete="CASCADE"),
        index=True,
    )

    # parent span (self-referencing)
    parent_span_id: Mapped[str | None] = mapped_column(
        ForeignKey("otel_spans.span_id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )

    span_name: Mapped[str] = mapped_column(String(255))
    span_kind: Mapped[str] = mapped_column(String(32))  # agent | engine | tool | llm | human

    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
    )
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    duration_ms: Mapped[int | None] = mapped_column(BigInteger)
    status: Mapped[str] = mapped_column(String(32))
    error_message: Mapped[str | None] = mapped_column(Text)

    # --- Relationships ---
    trace = relationship("DBTrace", back_populates="spans")

    parent = relationship(
        "DBSpan",
        remote_side="DBSpan.span_id",
        back_populates="children",
    )

    children = relationship(
        "DBSpan",
        back_populates="parent",
        cascade="all, delete-orphan",
    )

    attributes = relationship(
        "DBSpanAttribute",
        back_populates="span",
        cascade="all, delete-orphan",
    )

    events = relationship(
        "DBSpanEvent",
        back_populates="span",
        cascade="all, delete-orphan",
    )


class DBSpanAttribute(Base):
    __tablename__ = "span_attributes"

    id: Mapped[int] = mapped_column(primary_key=True)

    span_id: Mapped[str] = mapped_column(
        ForeignKey("otel_spans.span_id", ondelete="CASCADE"),
        index=True,
    )

    attribute_key: Mapped[str] = mapped_column(String(128), index=True)
    attribute_value: Mapped[dict] = mapped_column(JSON)

    span = relationship("DBSpan", back_populates="attributes")

class DBSpanEvent(Base):
    __tablename__ = "span_events"

    id: Mapped[int] = mapped_column(primary_key=True)

    span_id: Mapped[str] = mapped_column(
        ForeignKey("otel_spans.span_id", ondelete="CASCADE"),
        index=True,
    )

    event_name: Mapped[str] = mapped_column(String(128), index=True)
    event_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
    )

    event_data: Mapped[dict | None] = mapped_column(JSON)

    span = relationship("DBSpan", back_populates="events")


class DBMetric(Base):
    __tablename__ = "otel_metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), index=True)
    value: Mapped[float]
    labels: Mapped[dict | None] = mapped_column(JSON)
    trace_id: Mapped[str | None] = mapped_column(String(50), index=True)
    span_id: Mapped[str | None] = mapped_column(String(50), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
    )


# -------------------------------------------------------------------
# Base SQL Storage
# -------------------------------------------------------------------


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
                logger.warning(
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
                    logger.warning(
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
                print(f"End trace: {trace_id}")
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
