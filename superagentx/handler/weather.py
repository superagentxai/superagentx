import requests

from superagentx.handler.base import BaseHandler
from superagentx.handler.decorators import tool


class WeatherHandler(BaseHandler):

    @tool
    async def text_creation(self, latitude: str, longitude: str) -> dict:
        """
        Get the weather data based on given latitude & longitude.

        Args:
            @param latitude: latitude of the location
            @param longitude: longitude of the location

            @return result (Str): Return Fake Weather for the given city & name in Fahrenheit
        """

        url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current_weather=true"
        print(url)
        response = requests.get(url)
        print(response)
        return response.json()

    @tool
    async def get_lat_long(self, place: str) -> dict:

        """
        Get the coordinates of a city based on a location.

        Args:
            @param place:
            @param city (str): The place name

            @return result (Str): Return the real latitude & longitude for the given place.

        """

        header_dict = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
            "referer": 'https://www.guichevirtual.com.br'
        }
        url = "http://nominatim.openstreetmap.org/search"

        params = {'q': place, 'format': 'json', 'limit': 1}
        response = requests.get(url, params=params, headers=header_dict).json()
        if response:
            lat = response[0]["lat"]
            lon = response[0]["lon"]
            return {"latitude": lat, "longitude": lon}
        else:
            return None
