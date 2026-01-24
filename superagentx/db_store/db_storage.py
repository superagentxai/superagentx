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
from sqlalchemy import Enum as SQLEnum
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

from superagentx.db_store.db_interface import StorageAdapter
from superagentx.db_store.sql_status_enum import PipeStatus, AgentStatus

# -------------------------------------------------------------------
# Logging
# -------------------------------------------------------------------

logger = logging.getLogger(__name__)


# -------------------------------------------------------------------
# Time Utilities
# -------------------------------------------------------------------


def utcnow() -> datetime:
    """Return timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


# -------------------------------------------------------------------
# SQLAlchemy Base
# -------------------------------------------------------------------


class Base(DeclarativeBase):
    pass


# -------------------------------------------------------------------
# Models
# -------------------------------------------------------------------

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
            except IntegrityError:
                logger.info(
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

    async def close(self) -> None:
        """
        Properly close async engine and release all resources.
        Must be called BEFORE event loop shutdown.
        """
        if self.engine:
            await self.engine.dispose()
            logger.info("SQLAlchemy async engine disposed")


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
