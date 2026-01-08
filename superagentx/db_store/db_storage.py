from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Text, ForeignKey, DateTime, select, String, JSON
from sqlalchemy.exc import IntegrityError

from superagentx.db_store.db_interface import StorageAdapter


# --- Models ---

class Base(DeclarativeBase):
    pass


class DBPipe(Base):
    __tablename__ = "pipes"

    id: Mapped[int] = mapped_column(primary_key=True)
    pipe_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(30), default="Pending")
    error_details: Mapped[str] = mapped_column(Text, nullable=True)
    executed_by: Mapped[str] = mapped_column(String(100), nullable=True)
    updated_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    agents = relationship("DBAgent", back_populates="pipe")


class DBAgent(Base):
    __tablename__ = "agents"

    id: Mapped[int] = mapped_column(primary_key=True)
    pipe_id: Mapped[str] = mapped_column(ForeignKey("pipes.pipe_id"))
    agent_id: Mapped[str] = mapped_column(String(50), index=True)
    agent_name: Mapped[str] = mapped_column(String(50), index=True, nullable=True)
    content: Mapped[str] = mapped_column(String(50), index=True, nullable=True)
    result_data: Mapped[dict] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(30))
    updated_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    pipe = relationship("DBPipe", back_populates="agents")


# --- Base SQL Storage Implementation ---

class SQLBaseStorage(StorageAdapter):
    def __init__(self, connection_string: str):
        self.engine = create_async_engine(connection_string)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

    async def setup(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    # --- Pipe Operations ---

    async def pipe_exists(self, pipe_id: str) -> bool:
        """Checks if a pipe already exists in the database."""
        async with self.session_factory() as session:
            stmt = select(DBPipe).where(DBPipe.pipe_id == pipe_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none() is not None

    async def create_pipe(self, pipe_id: str, executed_by: str = "System"):
        """Creates a new pipe record. Silently handles existing IDs."""
        async with self.session_factory() as session:
            try:
                new_pipe = DBPipe(pipe_id=pipe_id, executed_by=executed_by, status="Pending")
                session.add(new_pipe)
                await session.commit()
            except IntegrityError:
                await session.rollback()

    async def update_pipe_status(self, pipe_id: str, status: str, error: str = None):
        async with self.session_factory() as session:
            stmt = select(DBPipe).where(DBPipe.pipe_id == pipe_id)
            result = await session.execute(stmt)
            pipe = result.scalar_one_or_none()
            if pipe:
                pipe.status = status
                pipe.error_details = error
                await session.commit()

    # --- Agent Operations ---

    async def is_agent_processed(self, pipe_id: str, agent_id: str) -> bool:
        """Checks if a specific agent in a specific pipe is already completed."""
        async with self.session_factory() as session:
            stmt = select(DBAgent).where(DBAgent.pipe_id == pipe_id, DBAgent.agent_id == agent_id)
            res = await session.execute(stmt)

            return res.scalar_one_or_none() is not None

    async def mark_agent_completed(
            self,
            pipe_id: str,
            agent_id: str,
            agent_name: str,
            status: str,
            goal_result: Any = None,
    ) -> None:
        """
        Persist agent completion status and optional goal result.
        """
        async with self.session_factory() as session, session.begin():
            # Normalize goal_result into a serializable dict/value
            if goal_result is None:
                result_dict = None
            elif hasattr(goal_result, "model_dump"):
                result_dict = goal_result.model_dump()
            else:
                result_dict = goal_result

            agent = DBAgent(
                pipe_id=pipe_id,
                agent_id=agent_id,
                agent_name=agent_name,
                result_data=result_dict,
                status=status,
            )

            session.add(agent)


# --- Specialized Storage Classes ---

class SQLiteStorage(SQLBaseStorage):
    """
    Implementation for SQLite.
    Requires: pip install aiosqlite
    """

    def __init__(self, db_path: str = "agents.db"):
        url = f"sqlite+aiosqlite:///{db_path}"
        super().__init__(url)


class PostgresStorage(SQLBaseStorage):
    """
    Implementation for PostgreSQL.
    Requires: pip install asyncpg
    """

    def __init__(self, host, user, password, db, port=5432):
        url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"
        super().__init__(url)
