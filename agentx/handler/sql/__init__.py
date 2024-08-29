from enum import Enum
from typing import Any

from sqlalchemy import create_engine, text

from agentx.handler.base import BaseHandler
from agentx.handler.sql.exceptions import InvalidDatabase


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

        self._engine = create_engine(url=self._conn_str)

    def _postgres_conn_str(self):
        if not self.port:
            self.port = 5432
        return f"postgresql+psycopg2://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

    def _mysql_or_mariadb_conn_str(self):
        if not self.port:
            self.port = 3306
        return (f"mysql+pymysql://{self.username}:{self.password}@"
                f"{self.host}:{self.port}/{self.database}?charset=utf8mb4")

    def _sqlite_conn_str(self):
        return f"sqlite+pysqlite:///{self.database}"

    def _oracle_conn_str(self):
        if not self.port:
            self.port = 1521
        return (f"oracle+oracledb://{self.username}:{self.password}@{self.host}:{self.port}"
                f"/?service_name={self.database}")

    def _mssql_conn_str(self):
        if not self.port:
            self.port = 1433
        return f"mssql+pymssql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}?charset=utf8"

    def handle(
            self,
            *,
            action: str | Enum,
            **kwargs
    ) -> Any:
        pass

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
        return self._stat_begin(stmt=stmt, values=values)

    def update(
            self,
            stmt: str,
            values: list[dict]
    ):
        return self._stat_begin(stmt=stmt, values=values)

    def delete(
            self,
            stmt: str,
            values: list[dict]
    ):
        return self._stat_begin(stmt=stmt, values=values)

    def create_table(
            self,
            stmt: str
    ):
        with self._engine.begin() as conn:
            return conn.execute(
                text(stmt)
            )

    def drop_table(self,
            stmt: str
    ):
        with self._engine.begin() as conn:
            return conn.execute(
                text(stmt)
            )

    def alter_table(self,
            stmt: str,
            values: list[dict]
    ):
        return self._stat_begin(stmt=stmt, values=values)

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

