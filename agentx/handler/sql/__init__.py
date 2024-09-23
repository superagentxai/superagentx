from enum import Enum
from typing import Any, final

from agentx.handler.base import BaseHandler
from agentx.handler.sql.exceptions import InvalidDatabase, InvalidSQLAction
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine


class SQLAction(str, Enum):
    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    CREATE_TABLE = "create_table"
    DROP_TABLE = "drop_table"
    ALTER_TABLE = "alter_table"


class SQLHandler(BaseHandler):

    def __init__(
            self,
            *,
            database_type: str,
            database: str,
            host: str | None = None,
            port: int | None = None,
            username: str | None = None,
            password: str | None = None
    ):
        self.database_type = database_type.lower()
        self.host = host or "localhost"
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        match self.database_type:
            case "postgres":
                self._conn_str = self._postgres_conn_str()
            case "mysql" | "mariadb":
                self._conn_str = self._mysql_or_mariadb_conn_str()
            case "sqlite":
                self._conn_str = self._sqlite_conn_str()
            case "oracle":
                self._conn_str = self._oracle_conn_str()
            case "mssql":
                self._conn_str = self._mssql_conn_str()
            case _:
                raise InvalidDatabase(f"Invalid database type `{self.database_type}`")


        self._engine = create_async_engine(url=self._conn_str)

    def _postgres_conn_str(self):
        if not self.port:
            self.port = 5432
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


    def _mysql_or_mariadb_conn_str(self):
        if not self.port:
            self.port = 3306
        return (f"mysql+aiomysql://{self.username}:{self.password}@"
                f"{self.host}:{self.port}/{self.database}?charset=utf8mb4")

    def _sqlite_conn_str(self):
        return f"sqlite+aiosqlite:///{self.database}"

    def _oracle_conn_str(self):
        return self._oracle_conn_str()

    def _mssql_conn_str(self):
        if not self.port:
            self.port = 1433
        return f"mssql+aioodbc://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}?charset=utf8"

    @final
    async def handle(
            self,
            *,
            action: str | Enum,
            **kwargs
    ) -> Any:
        if isinstance(action, str):
            action = action.lower()
        match action:
            case SQLAction.SELECT:
                return await self.select(**kwargs)
            case SQLAction.INSERT:
                return await self.insert(**kwargs)
            case SQLAction.UPDATE:
                return await self.update(**kwargs)
            case SQLAction.DELETE:
                return await self.delete(**kwargs)
            case SQLAction.CREATE_TABLE:
                return await self.create_table(**kwargs)
            case SQLAction.DROP_TABLE:
                return await self.drop_table(**kwargs)
            case SQLAction.ALTER_TABLE:
                return await self.alter_table(**kwargs)
            case _:
                raise InvalidSQLAction(f"Invalid sql action `{action}`")

    async def select(
            self,
            *,
            query: str
    ):
        async with self._engine.connect() as conn:
            res = await conn.execute(text(query))
            return res.all()

    async def insert(
            self,
            *,
            stmt: str,
            values: list[dict]
    ):
        return await self._stat_begin(
            stmt=stmt,
            values=values
        )

    async def update(
            self,
            *,
            stmt: str,
            values: list[dict]
    ):
        return await self._stat_begin(
            stmt=stmt,
            values=values
        )

    async def delete(
            self,
            *,
            stmt: str,
            values: list[dict]
    ):
        return await self._stat_begin(
            stmt=stmt,
            values=values
        )

    async def create_table(
            self,
            *,
            stmt: str
    ):
        async with self._engine.begin() as conn:
            return await conn.execute(
                text(stmt)
            )

    async def drop_table(
            self,
            *,
            stmt: str
    ):
        async with self._engine.begin() as conn:
            return await conn.execute(
                text(stmt)
            )

    async def alter_table(
            self,
            *,
            stmt: str,
            values: list[dict]
    ):
        return await self._stat_begin(
            stmt=stmt,
            values=values
        )

    async def _stat_begin(
            self,
            *,
            stmt: str,
            values: list[dict]
    ):
        async with self._engine.begin() as conn:
            return await conn.execute(
                text(stmt),
                values
            )

    def __dir__(self):
        return (
            'select',
            'insert',
            'update',
            'delete',
            'create_table',
            'drop_table',
            'alter_table'
        )
