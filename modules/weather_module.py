import requests
import logging

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

def get_weather_data(latitude, longitude, OPENWEATHER_API_KEY):
    """
    Fetches the current weather data for the given coordinates using the OpenWeatherMap API.
    Returns detailed weather information in a dictionary.
    """
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={OPENWEATHER_API_KEY}&units=metric"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx and 5xx)

        # Parse the JSON response
        data = response.json()

        # Extract weather details
        weather_data = {
            "temperature": data['main']['temp'],
            "feels_like": data['main']['feels_like'],
            "humidity": data['main']['humidity'],
            "pressure": data['main']['pressure'],
            "wind_speed": data['wind']['speed'],
            "wind_direction": data['wind']['deg'],
            "weather_description": data['weather'][0]['description'],
            "cloud_coverage": data['clouds']['all'],
            "visibility": data.get('visibility', 'Not available'),
            "sunrise": data['sys']['sunrise'],
            "sunset": data['sys']['sunset'],
            "location_name": data['name']
        }

        logging.info(f"Wetterdaten erfolgreich abgerufen für: {weather_data.get('location_name')}")
        return weather_data

    except requests.exceptions.RequestException as e:
        logging.error(f"Netzwerkfehler: {e}")
        return None
    except KeyError as e:
        logging.error(f"Fehler beim Verarbeiten der Daten: {e}")
        return None