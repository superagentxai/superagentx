from enum import Enum
from typing import Any

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
                self._aconn_str = self._apostgres_conn_str()
            case "mysql" | "mariadb":
                self._conn_str = self._mysql_or_mariadb_conn_str()
                self._aconn_str = self._amysql_or_mariadb_conn_str()
            case "sqlite":
                self._conn_str = self._sqlite_conn_str()
                self._aconn_str = self._asqlite_conn_str()
            case "oracle":
                self._conn_str = self._oracle_conn_str()
                self._aconn_str = self._aoracle_conn_str()
            case "mssql":
                self._conn_str = self._mssql_conn_str()
                self._aconn_str = self._amssql_conn_str()
            case _:
                raise InvalidDatabase(f"Invalid database type `{self.database_type}`")

        self._engine = create_engine(url=self._conn_str)
        self._aengine = create_async_engine(url=self._aconn_str)

    def _postgres_conn_str(self):
        if not self.port:
            self.port = 5432
        return f"postgresql+psycopg2://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

    def _apostgres_conn_str(self):
        if not self.port:
            self.port = 5432
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

    def _mysql_or_mariadb_conn_str(self):
        if not self.port:
            self.port = 3306
        return (f"mysql+pymysql://{self.username}:{self.password}@"
                f"{self.host}:{self.port}/{self.database}?charset=utf8mb4")

    def _amysql_or_mariadb_conn_str(self):
        if not self.port:
            self.port = 3306
        return (f"mysql+aiomysql://{self.username}:{self.password}@"
                f"{self.host}:{self.port}/{self.database}?charset=utf8mb4")

    def _sqlite_conn_str(self):
        return f"sqlite+pysqlite:///{self.database}"

    def _asqlite_conn_str(self):
        return f"sqlite+aiosqlite:///{self.database}"

    def _oracle_conn_str(self):
        if not self.port:
            self.port = 1521
        return (f"oracle+oracledb://{self.username}:{self.password}@{self.host}:{self.port}"
                f"/?service_name={self.database}")

    def _aoracle_conn_str(self):
        return self._oracle_conn_str()

    def _mssql_conn_str(self):
        if not self.port:
            self.port = 1433
        return f"mssql+pyodbc://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}?charset=utf8"

    def _amssql_conn_str(self):
        if not self.port:
            self.port = 1433
        return f"mssql+aioodbc://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}?charset=utf8"

    def handle(
            self,
            *,
            action: str | Enum,
            **kwargs
    ) -> Any:
        if isinstance(action, str):
            action = action.lower()
        match action:
            case SQLAction.SELECT:
                return self.select(**kwargs)
            case SQLAction.INSERT:
                return self.insert(**kwargs)
            case SQLAction.UPDATE:
                return self.update(**kwargs)
            case SQLAction.DELETE:
                return self.delete(**kwargs)
            case SQLAction.CREATE_TABLE:
                return self.create_table(**kwargs)
            case SQLAction.DROP_TABLE:
                return self.drop_table(**kwargs)
            case SQLAction.ALTER_TABLE:
                return self.alter_table(**kwargs)
            case _:
                raise InvalidSQLAction(f"Invalid sql action `{action}`")

    def select(
            self,
            query: str
    ):
        with self._engine.connect() as conn:
            return conn.execute(text(query)).all()

    def insert(
            self,
            stmt: str,
            values: list[dict]
    ):
        return self._stat_begin(
            stmt=stmt,
            values=values
        )

    def update(
            self,
            stmt: str,
            values: list[dict]
    ):
        return self._stat_begin(
            stmt=stmt,
            values=values
        )

    def delete(
            self,
            stmt: str,
            values: list[dict]
    ):
        return self._stat_begin(
            stmt=stmt,
            values=values
        )

    def create_table(
            self,
            stmt: str
    ):
        with self._engine.begin() as conn:
            return conn.execute(
                text(stmt)
            )

    def drop_table(
            self,
            stmt: str
    ):
        with self._engine.begin() as conn:
            return conn.execute(
                text(stmt)
            )

    def alter_table(
            self,
            stmt: str,
            values: list[dict]
    ):
        return self._stat_begin(
            stmt=stmt,
            values=values
        )

    def _stat_begin(
            self,
            stmt: str,
            values: list[dict]
    ):
        with self._engine.begin() as conn:
            return conn.execute(
                text(stmt),
                values
            )

    async def ahandle(
            self,
            *,
            action: str | Enum,
            **kwargs
    ) -> Any:
        if isinstance(action, str):
            action = action.lower()
        match action:
            case SQLAction.SELECT:
                return await self.aselect(**kwargs)
            case SQLAction.INSERT:
                return await self.ainsert(**kwargs)
            case SQLAction.UPDATE:
                return await self.aupdate(**kwargs)
            case SQLAction.DELETE:
                return await self.adelete(**kwargs)
            case SQLAction.CREATE_TABLE:
                return await self.acreate_table(**kwargs)
            case SQLAction.DROP_TABLE:
                return await self.adrop_table(**kwargs)
            case SQLAction.ALTER_TABLE:
                return await self.aalter_table(**kwargs)
            case _:
                raise InvalidSQLAction(f"Invalid sql action `{action}`")

    async def aselect(
            self,
            query: str
    ):
        async with self._aengine.connect() as conn:
            res = await conn.execute(text(query))
            return res.all()

    async def ainsert(
            self,
            stmt: str,
            values: list[dict]
    ):
        return await self._astat_begin(
            stmt=stmt,
            values=values
        )

    async def aupdate(
            self,
            stmt: str,
            values: list[dict]
    ):
        return await self._astat_begin(
            stmt=stmt,
            values=values
        )

    async def adelete(
            self,
            stmt: str,
            values: list[dict]
    ):
        return await self._astat_begin(
            stmt=stmt,
            values=values
        )

    async def acreate_table(
            self,
            stmt: str
    ):
        async with self._aengine.begin() as conn:
            return await conn.execute(
                text(stmt)
            )
    async def adrop_table(
            self,
            stmt: str
    ):
        async with self._aengine.begin() as conn:
            return await conn.execute(
                text(stmt)
            )

    async def aalter_table(
            self,
            stmt: str,
            values: list[dict]
    ):
        return await self._astat_begin(
            stmt=stmt,
            values=values
        )

    async def _astat_begin(
            self,
            stmt: str,
            values: list[dict]
    ):
        async with self._aengine.begin() as conn:
            return await conn.execute(
                text(stmt),
                values
            )
