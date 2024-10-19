from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from superagentx.handler.base import BaseHandler


class InvalidDatabase(Exception):
    pass


class InvalidSQLAction(Exception):
    pass


class SQLHandler(BaseHandler):
    """
        A handler class for managing SQL database operations.
        This class extends BaseHandler and provides methods to execute various SQL queries, such as creating,
        updating, deleting, and retrieving records from the database.
    """

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


    async def select(
            self,
            *,
            query: str
    ):
        """
            Asynchronously retrieves data based on the specified query string.
            This method executes a selection operation, returning relevant information according to the query criteria.

            parameters:
                 query (str):The main search query used to retrieve content. This is a required field and should be a
                descriptive string that accurately represents what content is being searched for.
                **kwargs: Additional keyword arguments that may be passed to customize the behavior of the handler.

            Returns:
                Any: The result of handling the action. The return type may vary depending on the specific action handled.

        """
        async with self._engine.connect() as conn:
            res = await conn.execute(text(query))
            return res.all()

    async def insert(
            self,
            *,
            stmt: str,
            values: list[dict]
    ):

        """
            Asynchronously inserts data into a database using the specified SQL statement and a list of value dictionaries.
            This method handles the execution of the insertion operation based on the provided parameters.

            parameters:
                 stmt (str): The SQL statement to be executed for the insertion, which should include placeholders
                 for values.
                 values (list[dict]): A list of dictionaries containing the values to be inserted, where each dictionary
                 represents a set of values corresponding to the placeholders in the SQL statement.

            Returns:
                Any: The result of handling the action. The return type may vary depending on the specific action handled.

        """

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

        """
        Asynchronously updates records in a database based on the provided SQL statement and a list of value
        dictionaries.This method manages the execution of the update operation to modify existing entries as specified.

        parameters:
                 stmt (str): The SQL statement to be executed for the insertion, which should include placeholders
                 for values.
                 values (list[dict]): A list of dictionaries containing the values to be inserted, where each dictionary
                 represents a set of values corresponding to the placeholders in the SQL statement.

            Returns:
                Any: The result of handling the action. The return type may vary depending on the specific action handled.
        """
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
        """

         Asynchronously deletes records from a database using the specified SQL statement and a list of value dictionaries.
         This method executes the deletion operation based on the provided parameters to remove specified entries.

         parameters:
                 stmt (str): The SQL statement to be executed for the insertion, which should include placeholders
                 for values.
                 values (list[dict]): A list of dictionaries containing the values to be inserted, where each dictionary
                 represents a set of values corresponding to the placeholders in the SQL statement.

            Returns:
                Any: The result of handling the action. The return type may vary depending on the specific action handled.

        """


        return await self._stat_begin(
            stmt=stmt,
            values=values
        )

    async def create_table(
            self,
            *,
            stmt: str
    ):

        """
        Asynchronously creates a new database table using the specified SQL statement.
        This method executes the table creation operation based on the provided SQL command.

         parameters:
            stmt (str): The SQL statement to be executed for the insertion, which should include placeholders
            for values.

        Returns:
            Any: The result of handling the action. The return type may vary depending on the specific action handled.

        """
        async with self._engine.begin() as conn:
            return await conn.execute(
                text(stmt)
            )

    async def drop_table(
            self,
            *,
            stmt: str
    ):
        """
        Asynchronously drops an existing database table using the specified SQL statement.
        This method executes the table removal operation based on the provided SQL command.

         parameters:
            stmt (str): The SQL statement to be executed for the insertion, which should include placeholders
            for values.

         Returns:
            Any: The result of handling the action. The return type may vary depending on the specific action handled.

        """
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
        """
        Asynchronously alters an existing database table using the specified SQL statement and a list of value dictionaries.
        This method executes the alteration operation to modify the table structure as defined by the provided parameters.

        parameters:
             stmt (str): The SQL statement to be executed for the insertion, which should include placeholders
             for values.
             values (list[dict]): A list of dictionaries containing the values to be inserted, where each dictionary
             represents a set of values corresponding to the placeholders in the SQL statement.

        Returns:
            Any: The result of handling the action. The return type may vary depending on the specific action handled.

        """

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
        """
        Asynchronously begins a statistical operation using the specified SQL statement and a list of value dictionaries.
        This method sets up the context for performing statistical analysis based on the provided parameters.

        parameters:
             stmt (str): The SQL statement to be executed for the insertion, which should include placeholders
             for values.
             values (list[dict]): A list of dictionaries containing the values to be inserted, where each dictionary
             represents a set of values corresponding to the placeholders in the SQL statement.

        Returns:
            Any: The result of handling the action. The return type may vary depending on the specific action handled.

        """

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
