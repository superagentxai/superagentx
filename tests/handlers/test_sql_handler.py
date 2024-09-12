from agentx.handler.sql import SQLHandler

sql_handler = SQLHandler(
      database_type="sqlite",
      database="/tmp/sample.db"
)


def test_create_table():
    res = sql_handler.handle(action="CREATE_TABLE", stmt="CREATE TABLE test (x int, y int)")
    print("Create table res => ", res)


def test_insert_table():
    res = sql_handler.handle(
        action="INSERT",
        stmt="INSERT INTO test (x, y) VALUES (:x, :y)",
        values=[{'x': 1, 'y': 2}, {'x': 2, 'y': 4}]
    )
    print("Insert row res => ", res)


def test_select_table():
    res = sql_handler.handle(
        action="SELECT",
        query="SELECT * from test"
    )
    print(res)
    assert len(res) > 0


def test_drop_table():
    res = sql_handler.handle(
        action="DROP_TABLE",
        stmt="DROP TABLE test"
    )
    print(res)
