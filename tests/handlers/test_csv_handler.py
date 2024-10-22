import pytest

from superagentx.handler.csv_data import CsvHandler

'''
Run Pytest:

    1.pytest --log-cli-level=INFO tests/handlers/test_csv_handler.py::TestCSV::test_csv_handler

'''

@pytest.fixture
def csv_client_init() -> CsvHandler:
    input = ""
    csv_handler = CsvHandler(
        csv_path=input
    )
    return csv_handler

class TestCSV:
    async def test_csv_handler(self, csv_client_init: CsvHandler):
        query = "who are all Petroleum engineer?"
        res = await csv_client_init.search(query)
        assert isinstance(res, object)
