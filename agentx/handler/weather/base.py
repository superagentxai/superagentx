import openmeteo_requests
import requests_cache
from agentx.handler.weather.exception import WeatherApiException, WeatherNotFound
from retry_requests import retry


class  WeatherBase:

    def __init__(
            self,
            *,
            params: dict,
            url: str,
            api_key: str | None
    ):
        self.params = params
        self.api_key = api_key
        self.url = url


    def get_weather_report(self):
        try:
            # Setup the Open-Meteo API client with cache and retry on error
            cache_session = requests_cache.CachedSession(
                cache_name='.cache',
                expire_after=3600
            )
            retry_session = retry(
                session=cache_session,
                retries=5,
                backoff_factor=0.2
            )
            open_meteo = openmeteo_requests.Client(session=retry_session)
            if self.api_key:
                self.params['apikey'] = self.api_key

            response = open_meteo.weather_api(
                url=self.url,
                params=self.params
            )
            if response and response[0]:
                return response
            else:
                raise WeatherNotFound("Weather not found")
        except Exception as ex:
            raise WeatherApiException('Error: failed api request', ex)



