from agentx.handler.sql import SQLHandler


sql_handler = SQLHandler(
    database_type="sqlite",
    database="/tmp/sample.db"
)


async def test_sqlite_1():
    res = await sql_handler.ahandle(
        action="CREATE_TABLE",
        stmt="CREATE TABLE test (x int, y int)"
    )
    print("Create table res => ", res)


async def test_sqlite_2():
    res = await sql_handler.ahandle(
        action="INSERT",
        stmt="INSERT INTO test (x, y) VALUES (:x, :y)",
        values=[{'x': 1, 'y': 2}, {'x': 2, 'y': 4}]
    )
    print("Insert row res => ", res)


async def test_sqlite_3():
    res = await sql_handler.ahandle(
        action="SELECT",
        query="SELECT * from test"
    )
    print(res)
    assert len(res) > 0


async def test_sqlite_4():
    res = await sql_handler.ahandle(
        action="DROP_TABLE",
        stmt="DROP TABLE test"
    )
    print(res)
