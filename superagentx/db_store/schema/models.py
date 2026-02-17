from datetime import datetime
from sqlalchemy import (
    DateTime, ForeignKey, JSON, String, Text, UniqueConstraint, BigInteger
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from superagentx.db_store.sql_status_enum import PipeStatus, AgentStatus
from superagentx.utils.helper import utcnow


# Shared Base Class
class Base(DeclarativeBase):
    pass

# --- Workflow Schema ---

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

# --- Telemetry Schema (OpenTelemetry Style) ---

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