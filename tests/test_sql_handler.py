from agentx.handler.sql import SQLHandler

sql_handler = SQLHandler(database_type="sqlite", database="/tmp/sample.db")


def test_sqlite_1():
    res = sql_handler.create_table("CREATE TABLE test (x int, y int)")
    print("Create table res => ", res)


def test_sqlite_2():
    res = sql_handler.insert(
        "INSERT INTO test (x, y) VALUES (:x, :y)",
        values=[{'x': 1, 'y': 2}, {'x': 2, 'y': 4}]
    )
    print("Insert row res => ", res)


def test_sqlite_3():
    res = sql_handler.select(
        "SELECT * from test"
    )
    print(res)
    assert len(res) > 0


def test_sqlite_4():
    res = sql_handler.drop_table(
        "DROP TABLE test"
    )
    print(res)
