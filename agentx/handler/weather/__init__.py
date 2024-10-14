from enum import StrEnum

import pandas as pd
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

from agentx.handler.base import BaseHandler
from agentx.handler.weather.base import WeatherBase
from agentx.handler.weather.constants import MARINE_CURRENT_STATUS_VARIABLE, MARINE_DAILY_STATUS_VARIABLE, \
    MARINE_HOURLY_STATUS_VARIABLE, AIR_CURRENT_STATUS_VARIABLE, AIR_HOURLY_STATUS_VARIABLE, \
    CLIMATE_MODELS_STATUS_VARIABLE, CLIMATE_DAILY_STATUS_VARIABLE, HISTORICAL_DAILY_STATUS_VARIABLE, \
    HISTORICAL_HOURLY_STATUS_VARIABLE, FORCAST_CURRENT_STATUS_VARIABLE, FORECAST_HOURLY_STATUS_VARIABLE, \
    FORECAST_DAILY_STATUS_VARIABLE, FLOOD_MODELS_STATUS_VARIABLE, FLOOD_DAILY_STATUS_VARIABLE, FORCAST_API_URL, \
    HISTORICAL_API_URL, CLIMATE_API_URL, MARINE_API_URL, AIR_API_URL, FLOOD_API_URL
from agentx.handler.weather.exception import InvalidWeatherAction, InvalidLocation, InvalidResponseType
from agentx.utils.helper import sync_to_async


class ResponseType(StrEnum):
    current = 'current'
    daily = 'daily'
    hourly = 'hourly'


async def get_longitude(location):
    if location:
        geolocator = Nominatim(user_agent="WeatherTest")
        location = await sync_to_async(geolocator.geocode,location)
        return location.longitude
    else:
        raise InvalidLocation(f"Location {location} is not valid")


async def get_latitude(location):
    if location:
        geolocator = Nominatim(user_agent="WeatherTest")
        location = await sync_to_async(geolocator.geocode,location)
        return location.latitude
    else:
        raise InvalidLocation(f"Location {location} is not valid")


async def get_default_params(location: str) -> dict:
    tz = TimezoneFinder()
    lat = await get_latitude(location)
    lng = await get_longitude(location)
    param = {
        "latitude": lat,
        "longitude":lng,
        "timezone": tz.timezone_at(lng=lng, lat=lat)
    }
    return param

async def get_result_parser(
        *,
        response,
        variables,
        res_type: ResponseType
):
    result = {}
    data ={}
    if response and response[0]:
        if res_type == ResponseType.hourly:
            data = response[0].Hourly()
        elif res_type == ResponseType.daily:
            data = response[0].Daily()
        elif res_type == ResponseType.current:
            data = response[0].Current()
        else:
            raise InvalidResponseType("Invalid response type")

    if res_type != ResponseType.current:
        result = {"date": pd.date_range(
            start=pd.to_datetime(data.Time(), unit="s", utc=True),
            end=pd.to_datetime(data.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=data.Interval()),
            inclusive="left"
        )}
        for idx, item in enumerate(variables):
            result[item] = data.Variables(idx).ValuesAsNumpy()
    else:
        for idx, item in enumerate(variables):
            result[item] = data.Variables(idx).Value()
        result = [result]

    dataframe = pd.DataFrame(data=result)
    return dataframe


class WeatherHandler(BaseHandler):
    """
        A handler class for managing various weather-related data operations.
        This class extends BaseHandler and provides methods to retrieve different types of weather information,
        such as forecasts, historical data, air quality, marine conditions, and climate trends.
    """

    def __init__(
            self,
            api_key: str | None = None,
    ):
        self.api_key = api_key


    async def get_historical_weather(
            self,
            *,
            location: str,
            start_date:str,
            end_date:str,
            daily:bool,
            hourly: bool
    ):

        """
        Asynchronously retrieves historical weather data for a specified location.
        This method provides past weather conditions, including temperature, precipitation, and other relevant metrics.

        parameter:
            location (str): The location for which the scheduling or event is being created.
            start_date (str): The start date of the event, formatted as a string (e.g., 'YYYY-MM-DD').
            end_date (str): The end date of the event, formatted as a string (e.g., 'YYYY-MM-DD').
            daily (bool): A flag indicating whether the event recurs daily.
            hourly (bool): A flag indicating whether the event recurs hourly.

        """

        params = await get_default_params(location)
        params['start_date'] =start_date,
        params['end_date'] = end_date,
        response = {}
        if daily:
            params['daily'] = HISTORICAL_DAILY_STATUS_VARIABLE
        if hourly:
            params['hourly'] = HISTORICAL_HOURLY_STATUS_VARIABLE

        obj = WeatherBase(
            params=params,
            url=HISTORICAL_API_URL,
            api_key=self.api_key
        )
        res = obj.get_weather_report()
        if daily:
            response['daily'] = await get_result_parser(
                response=res,
                variables=HISTORICAL_DAILY_STATUS_VARIABLE,
                res_type=ResponseType.daily
            )
        if hourly:
            response['hourly'] = await get_result_parser(
                response=res,
                variables=HISTORICAL_HOURLY_STATUS_VARIABLE,
                res_type=ResponseType.hourly
            )
        return response

    async def get_forecast_weather(
            self,
            *,
            location: str,
            forecast_days:int,
            past_days: int,
            current:bool,
            daily:bool,
            hourly: bool
    ):
        """
        Asynchronously retrieves weather forecast data for a specified location.
        This method provides upcoming weather conditions, including temperature, precipitation, and wind predictions.

        parameter:
            location (str): The location for which the weather data is being requested.
            forecast_days (int): The number of days for which to retrieve the weather forecast.
            past_days (int): The number of past days for which to retrieve historical weather data.
            current (bool): A flag indicating whether to include current weather conditions in the response.
            daily (bool): A flag indicating whether to retrieve daily weather data.
            hourly (bool): A flag indicating whether to retrieve hourly weather data.

        """


        params = await get_default_params(location)
        response = {}
        if forecast_days and 0 < forecast_days:
            params['forecast_days'] = forecast_days,
        if past_days and 0 < past_days:
            params['past_days'] = past_days,

        if current:
            params['current'] = FORCAST_CURRENT_STATUS_VARIABLE
        if daily:
            params['daily'] = FORECAST_DAILY_STATUS_VARIABLE
        if hourly:
            params['hourly'] = FORECAST_HOURLY_STATUS_VARIABLE

        obj = WeatherBase(
            params=params,
            url=FORCAST_API_URL,
            api_key=self.api_key
        )
        res = await sync_to_async(obj.get_weather_report)
        if current:
            response['current'] = await get_result_parser(
                response=res,
                variables=FORCAST_CURRENT_STATUS_VARIABLE,
                res_type=ResponseType.current
            )
        if daily:
            response['daily'] = await get_result_parser(
                response=res,
                variables=FORECAST_DAILY_STATUS_VARIABLE,
                res_type=ResponseType.daily
            )
        if hourly:
            response['hourly'] = await get_result_parser(
                response=res,
                variables=FORECAST_HOURLY_STATUS_VARIABLE,
                res_type=ResponseType.hourly
            )
        return response

    async def get_climate_weather(
            self,
            *,
            location: str,
            start_date: str,
            end_date: str,
            daily: bool
    ):
        """
         Asynchronously retrieves climate-related weather data for a specified region.
         This method provides long-term climate trends and patterns, including temperature and precipitation data.

        parameter:
            location (str): The location for which the weather data is being requested.
            start_date (str): The start date of the event, formatted as a string (e.g., 'YYYY-MM-DD').
            end_date (str): The end date of the event, formatted as a string (e.g., 'YYYY-MM-DD').
            daily (bool): A flag indicating whether to retrieve daily weather data.

        """


        params = await get_default_params(location)
        params['start_date'] = start_date,
        params['end_date'] = end_date,
        params['models'] = CLIMATE_MODELS_STATUS_VARIABLE,
        response = {}
        if daily:
            params['daily'] = CLIMATE_DAILY_STATUS_VARIABLE
        obj = WeatherBase(
            params=params,
            url=CLIMATE_API_URL,
            api_key=self.api_key
        )
        res = await sync_to_async(obj.get_weather_report)
        if daily:
            response['daily'] = await get_result_parser(
                response=res,
                variables=CLIMATE_DAILY_STATUS_VARIABLE,
                res_type=ResponseType.daily
            )
        return response

    async def get_marine_weather(
            self,
            *,
            location: str,
            forecast_days: int,
            past_days: int,
            current: bool,
            daily: bool,
            hourly: bool
    ):
        """
        Asynchronously retrieves marine weather data for a specified coastal or oceanic location.
        This method provides information on sea conditions, tides, and weather impacting marine environments.

        parameter:
            location (str): The location for which to retrieve weather data.
            forecast_days (int): The number of days to include in the weather forecast.
            past_days (int): The number of past days for which to gather historical weather data.
            current (bool): A flag indicating whether to include current weather conditions.
            daily (bool): A flag indicating whether to fetch daily weather data.
            hourly (bool): A flag indicating whether to fetch hourly weather data.

        """


        params = await sync_to_async(get_default_params, location)
        response = {}
        if forecast_days and 0 < forecast_days:
            params['forecast_days'] = forecast_days,
        if past_days and 0<past_days:
            params['past_days'] = past_days,
        if current:
            params['current'] = MARINE_CURRENT_STATUS_VARIABLE
        if daily:
            params['daily'] = MARINE_DAILY_STATUS_VARIABLE
        if hourly:
            params['hourly'] = MARINE_HOURLY_STATUS_VARIABLE
        obj = WeatherBase(
            params=params,
            url=MARINE_API_URL,
            api_key=self.api_key
        )
        res = obj.get_weather_report()
        if current:
            response['current'] = get_result_parser(
                response=res,
                variables=MARINE_CURRENT_STATUS_VARIABLE,
                res_type=ResponseType.current
            )
        if daily:
            response['daily'] = get_result_parser(
                response=res,
                variables=MARINE_DAILY_STATUS_VARIABLE,
                res_type=ResponseType.daily
            )
        if hourly:
            response['hourly'] = get_result_parser(
                response=res,
                variables=MARINE_HOURLY_STATUS_VARIABLE,
                res_type=ResponseType.hourly
            )
        return response

    async def get_air_quality_weather(
            self,
            *,
            location: str,
            forecast_days: int,
            past_days: int,
            current: bool,
            hourly: bool
    ):
        """
        Asynchronously retrieves air quality data for a specified location.
        This method provides information on current air quality levels and related weather conditions.

        parameter:
            location (str): The location for which to retrieve weather data.
            forecast_days (int): The number of days to include in the weather forecast.
            past_days (int): The number of past days for which to gather historical weather data.
            current (bool): A flag indicating whether to include current weather conditions.
            hourly (bool): A flag indicating whether to fetch hourly weather data.

        """


        params = await sync_to_async(get_default_params,location)
        response = {}
        if forecast_days and 0<forecast_days:
            params['forecast_days'] = forecast_days,
        if past_days and 0<past_days:
            params['past_days'] = past_days,
        if current:
            params['current'] = AIR_CURRENT_STATUS_VARIABLE
        if hourly:
            params['hourly'] = AIR_HOURLY_STATUS_VARIABLE
        obj = WeatherBase(
            params=params,
            url=AIR_API_URL,
            api_key=self.api_key
        )
        res = obj.get_weather_report()
        if current:
            response['current'] = get_result_parser(
                response=res,
                variables=AIR_CURRENT_STATUS_VARIABLE,
                res_type=ResponseType.current
            )
        if hourly:
            response['hourly'] = get_result_parser(
                response=res,
                variables=AIR_HOURLY_STATUS_VARIABLE,
                res_type=ResponseType.hourly
            )
        return response

    async def get_flood_weather(
            self,
            location: str,
            forecast_days: int,
            past_days: int,
            daily: bool
    ):
        """
        Asynchronously retrieves flood-related weather information for the specified location.
        This method provides updates on flood risks and weather conditions contributing to potential flooding.

        parameter:
            location (str): The location for which to retrieve weather data.
            forecast_days (int): The number of days to include in the weather forecast.
            past_days (int): The number of past days for which to gather historical weather data.
            daily (bool): A flag indicating whether to fetch daily weather data.

        """


        params = await sync_to_async(get_default_params,location)
        params['models'] = FLOOD_MODELS_STATUS_VARIABLE
        response = {}
        if forecast_days and 0 < forecast_days:
            params['forecast_days'] = forecast_days,
        if past_days and 0<past_days:
            params['past_days'] = past_days,
        if daily:
            params['daily'] = FLOOD_DAILY_STATUS_VARIABLE
        obj = WeatherBase(
            params=params,
            url=FLOOD_API_URL,
            api_key=self.api_key
        )
        res = obj.get_weather_report()
        if daily:
            response['daily'] = get_result_parser(
                response=res,
                variables=FLOOD_DAILY_STATUS_VARIABLE,
                res_type=ResponseType.daily
            )
        return response


    def __dir__(self):
        return (
            'forecast_weather',
            'historical_weather',
            'climate_weather',
            'flood_weather',
            'air_quality_weather',
            'marine_weather'
        )

