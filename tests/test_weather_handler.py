from agentx.handler.weather import WeatherHandler

# API KEY is required if commercial. otherwise not required
w_handler = WeatherHandler(api_key='<API_KEY>')

def test_forecast_weather():
    res = w_handler.handle(location="chennai",forecast_days=3,action="forecast")
    assert res

def test_historical_weather():
    res = w_handler.handle(location="chennai",forecast_days=3,action="historical")
    assert res

def test_climate_weather():
    res = w_handler.handle(location="chennai",forecast_days=3,action="climate")
    assert res

def test_flood_weather():
    res = w_handler.handle(location="chennai",forecast_days=3,action="flood")
    assert res
def test_air_quality_weather():
    res = w_handler.handle(location="chennai",forecast_days=3,action="air_quality")
    assert res
def test_marine_weather():
    res = w_handler.handle(location="chennai",forecast_days=3,action="marine")
    assert res




