import os
from dotenv import load_dotenv
from weather_module import get_weather_data
from shelly_module import get_shelly_environment
from humidity_calculator import plot_humidity_curve

def main():
     # Laden der Umgebungsvariablen
    load_dotenv()

    api_key = os.getenv("API_KEY")
    latitude = float(os.getenv("LATITUDE"))
    longitude = float(os.getenv("LONGITUDE"))
    shelly_ip = os.getenv("SHELLY_IP")

    # Raumdaten vom Shelly abrufen
    indoor_temp, _ = get_shelly_environment(shelly_ip)
    if indoor_temp is None:
        print("Fehler: Raumtemperatur konnte nicht vom Shelly abgerufen werden.")
        return

    print(f"Raumtemperatur: {indoor_temp}°C")

    # Wetterdaten abrufen
    temp, humidity = get_weather_data(latitude, longitude, api_key)
    if temp is None or humidity is None:
        print("Fehler: Es konnten keine Wetterdaten abgerufen werden.")
        return

    print(f"Aktuelle Außentemperatur: {temp}°C")
    print(f"Relative Luftfeuchtigkeit draußen: {humidity}%")

    # Diagramm erstellen
    plot_humidity_curve(temp, humidity, indoor_temp)

if __name__ == "__main__":
    main()