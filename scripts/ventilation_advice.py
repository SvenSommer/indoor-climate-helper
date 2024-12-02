import os
from dotenv import load_dotenv
from modules.weather_module import get_weather_data
from modules.shelly_module import get_shelly_environment
from modules.humidity_calculator import calculate_relative_humidity

def main():
    # Laden der Umgebungsvariablen
    load_dotenv()

    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
    latitude = float(os.getenv("LATITUDE"))
    longitude = float(os.getenv("LONGITUDE"))
    shelly_ip = os.getenv("SHELLY_IP")

    # Ziel-Luftfeuchtigkeit und minimale Raumtemperatur
    min_indoor_temp = 18.0

    # Raumklimadaten abrufen
    indoor_temp, indoor_humidity = get_shelly_environment(shelly_ip)
    if indoor_temp is None or indoor_humidity is None:
        print("Fehler: Temperatur oder Luftfeuchtigkeit konnte nicht vom Shelly abgerufen werden.")
        return

    print(f"Raumtemperatur: {indoor_temp}°C")
    print(f"Raumluftfeuchtigkeit: {indoor_humidity}%")

    # Wetterdaten abrufen
    temp, humidity = get_weather_data(latitude, longitude, OPENWEATHER_API_KEY)
    if temp is None or humidity is None:
        print("Fehler: Es konnten keine Wetterdaten abgerufen werden.")
        return

    print(f"Aktuelle Außentemperatur: {temp}°C")
    print(f"Relative Luftfeuchtigkeit draußen: {humidity}%")

    # Relative Luftfeuchtigkeit der Außenluft nach Erwärmung berechnen
    outside_humidity_after_heating = calculate_relative_humidity(temp, humidity, indoor_temp)
    print(f"Relative Luftfeuchtigkeit draußen nach Erwärmung: {outside_humidity_after_heating:.2f}%")

    # Entscheidung basierend auf Bedingungen
    if indoor_temp <= min_indoor_temp:
        print(f"Es ist zu kalt zum Lüften (Raumtemperatur: {indoor_temp}°C).")
    elif outside_humidity_after_heating < indoor_humidity:
        print(f"Lüften ist sinnvoll. Die relative Luftfeuchtigkeit könnte von {indoor_humidity}% auf {outside_humidity_after_heating:.2f}% sinken.")
    else:
        print(f"Lüften ist nicht sinnvoll. Außenluft verbessert die Raumfeuchtigkeit nicht.")

if __name__ == "__main__":
    main()