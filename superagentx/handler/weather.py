import requests


class WeatherHandler(BaseHandler):

    async def get_lat_long(self, place: str) -> dict:

        """
        Get the coordinates of a city based on a location.

        Args:
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

    async def get_weather(self, city: str, state: str) -> str:
        """
        Get weather of a location.

        Args:
            @param state: The city name
            @param city: The state name

            @return result (Str): Return Fake Weather for the given city & name in Fahrenheit
        """
        result = f'Weather in {city}, {state} is 70F and clear skies.'
        print(f'Tool result: {result}')
        return result

    def __dir__(self):
        """
         Publish a list of method names that should be considered by an LLM if the corresponding methods are eligible to invoke.
        """
        return ([
            'get_weather',
        ]
        )
