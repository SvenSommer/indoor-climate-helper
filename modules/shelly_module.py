import requests

def get_shelly_environment(shelly_ip):
    """
    Fetches the current room temperature and humidity from the Shelly device.
    """
    try:
        url = f"http://{shelly_ip}/status"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            # Temperatur und Luftfeuchtigkeit extrahieren
            temperature = data["temperature:0"]["tC"]
            humidity = data["humidity:0"]["rh"]
            return temperature, humidity
        else:
            print(f"Fehler beim Abrufen der Shelly-Daten: {response.status_code}")
            return None, None
    except Exception as e:
        print(f"Fehler: {e}")
        return None, None