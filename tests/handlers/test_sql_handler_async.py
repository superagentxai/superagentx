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
        database_type="sqlite",
        database="/tmp/sample.db"
    )
    return sql_handler

class TestSql:

    async def test_create_table(self, sql_client_init: SQLHandler):
        stmt = "CREATE TABLE test (x int, y int)"
        res = await sql_client_init.ahandle(action="CREATE_TABLE",
                                            stmt=stmt
                                            )
        res_dict = res.context.__dict__
        logger.info(f"Create Table: {res.context.__dict__}")
        assert isinstance(res, CursorResult)
        assert stmt == res_dict.get("statement")


    async def test_insert_table(self, sql_client_init: SQLHandler):
        stmt="INSERT INTO test (x, y) VALUES (:x, :y)",
        values=[{'x': 1, 'y': 2}, {'x': 2, 'y': 4}]
        res = await sql_client_init.ahandle(
                action="INSERT",
                stmt=stmt,
                values=values
        )
        res_dict = res.context.__dict__
        logger.info(f"Insert Table: {res.context.__dict__}")
        assert isinstance(res, CursorResult)
        assert len(values) == res_dict.get("_rowcount")


    async def test_select_table(self, sql_client_init: SQLHandler):
        res = await sql_client_init.ahandle(
            action="SELECT",
            query="SELECT * from test"
        )
        logger.info(f"query Result: {res}")
        assert len(res) > 0


    async def test_drop_table(self, sql_client_init: SQLHandler):
        res = await sql_client_init.ahandle(
            action="DROP_TABLE",
            stmt="DROP TABLE test"
        )
        res_dict = res.context.__dict__
        assert isinstance(res, CursorResult)
