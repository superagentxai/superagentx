import pytest
import logging

from agentx.handler.sql import SQLHandler
from sqlalchemy.engine.cursor import CursorResult

logger = logging.getLogger(__name__)

'''
 Run Pytest:  

    1.pytest --log-cli-level=INFO tests/handlers/test_sql_handler_async.py::TestSql::test_create_table
    2.pytest --log-cli-level=INFO tests/handlers/test_sql_handler_async.py::TestSql::test_insert_table
    3.pytest --log-cli-level=INFO tests/handlers/test_sql_handler_async.py::TestSql::test_select_table
    4.pytest --log-cli-level=INFO tests/handlers/test_sql_handler_async.py::TestSql::test_drop_table
    
'''

@pytest.fixture
def sql_client_init() -> SQLHandler:
    sql_handler = SQLHandler(
        database_type="mysql",
        database="test",
        username="root",
        password="df_12345"
    )
    return sql_handler


class TestSql:

        async def test_create_table(self, sql_client_init: SQLHandler):
            stmt = "CREATE TABLE test9 (x int, y int)"
            res = await sql_client_init.create_table( stmt=stmt)
            res_dict = res.context.__dict__
            logger.info(f"Create Table: {res.context.__dict__}")
            assert isinstance(res, CursorResult)
            assert stmt == res_dict.get("statement")

        async def test_insert_table(self, sql_client_init: SQLHandler):
            stmt = "INSERT INTO test9 (x, y) VALUES (:x, :y)"
            values = [{'x': 1, 'y': 2}, {'x': 2, 'y': 4}]
            res = await sql_client_init.insert(
                stmt=stmt,
                values=values
            )

            res_dict = res.context.__dict__
            logger.info(f"Insert Table: {res.context.__dict__}")
            assert isinstance(res, CursorResult)
            assert len(values) == res_dict.get("_rowcount")

        async def test_select_table(self, sql_client_init: SQLHandler):
            res = await sql_client_init.select(
                query="SELECT * from test9"
            )
            logger.info(f"Query Result: {res}")
            assert len(res) > 0

        async def test_drop_table(self, sql_client_init: SQLHandler):
            res = await sql_client_init.drop_table(
                stmt="DROP TABLE test9"
            )
            res_dict = res.context.__dict__
