from agentx.handler.google.calender import CalenderHandler

calender_handler = CalenderHandler(
    credentials="/Users/arulvivek/Desktop/Agentx/credentials.json"
)


async def test_today_events():
    res = await calender_handler.get_today_events()
    print(res)


def test_week_events():
    res = calender_handler.get_week_events()
    print(res)


def test_month_events():
    res = calender_handler.get_month_events()
    print(res)


def test_get_events_by_type():
    res = calender_handler.get_events_by_type(
        eventType="default"
    )
    print(res)
