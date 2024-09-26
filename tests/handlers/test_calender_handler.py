import logging

import pytest

from agentx.handler.google.calender import CalenderHandler

logger = logging.getLogger(__name__)

'''
 Run Pytest:  

   1.pytest --log-cli-level=INFO tests/handlers/test_calender_handler.py::TestCalendar::test_today_events
   2.pytest --log-cli-level=INFO tests/handlers/test_calender_handler.py::TestCalendar::test_week_events
   3.pytest --log-cli-level=INFO tests/handlers/test_calender_handler.py::TestCalendar::test_month_events
   4.pytest --log-cli-level=INFO tests/handlers/test_calender_handler.py::TestCalendar::test_get_events_by_type

'''


@pytest.fixture
def google_calender_init() -> CalenderHandler:
    calender_handler = CalenderHandler(
        credentials=""
    )
    return calender_handler


class TestCalendar:

    async def test_today_events(self, google_calender_init: CalenderHandler):
        res = await google_calender_init.get_today_events()
        logger.info(f"Result: {res}")
        assert "items" in res

    async def test_week_events(self, google_calender_init: CalenderHandler):
        res = await google_calender_init.get_week_events()
        logger.info(f"Result: {res}")
        assert "items" in res

    async def test_month_events(self, google_calender_init: CalenderHandler):
        res = await google_calender_init.get_month_events()
        logger.info(f"Result: {res}")
        assert "items" in res

    async def test_get_events_by_type(self, google_calender_init: CalenderHandler):
        res = await google_calender_init.get_events_by_type(
            event_type="default"
        )
        logger.info(f"Result: {res}")
        assert "items" in res
