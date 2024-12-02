import requests

def get_weather_data(latitude, longitude, OPENWEATHER_API_KEY):
    """
    Fetches the current weather data for the given coordinates using the OpenWeatherMap API.
    """
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={OPENWEATHER_API_KEY}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        temperature = data['main']['temp']
        humidity = data['main']['humidity']
        return temperature, humidity
    else:
        print("Fehler beim Abrufen der Wetterdaten:", response.status_code)
        print("Antwort:", response.text)
        return None, None