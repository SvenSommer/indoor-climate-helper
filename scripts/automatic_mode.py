import os
import time
from dotenv import load_dotenv
from modules.weather_module import get_weather_data
from modules.shelly_module import get_shelly_environment
from modules.humidity_calculator import calculate_relative_humidity, max_absolute_humidity
from modules.dehumidifier_module import DehumidifierController
from hashlib import sha256

# Constants
DEFAULT_HUMIDITY_DIFFERENCE = 10.0
DEFAULT_TARGET_HUMIDITY = 50
DEFAULT_MIN_INDOOR_TEMP = 18
WAIT_TIME_SECONDS = 300  # 300 equals 5 minutes

def load_environment_variables():
    """Loads and validates environment variables."""
    load_dotenv()
    try:
        return {
            "OPENWEATHER_API_KEY": os.getenv("OPENWEATHER_API_KEY"),
            "latitude": float(os.getenv("LATITUDE")),
            "longitude": float(os.getenv("LONGITUDE")),
            "shelly_ip": os.getenv("SHELLY_IP"),
            "dehumidifier_email": os.getenv("DEHUMIDIFIER_EMAIL"),
            "dehumidifier_password": os.getenv("DEHUMIDIFIER_PASSWORD"),
            "dehumidifier_debug_mode": os.getenv("DEHUMIDIFIER_DEBUG_MODE") == "True",
            "dehumidifier_verbose_mode": os.getenv("DEHUMIDIFIER_VERBOSE_MODE") == "True",
            "humidity_difference": float(os.getenv("HUMIDITY_DIFFERENCE", DEFAULT_HUMIDITY_DIFFERENCE)),
            "target_humidity": int(os.getenv("TARGET_HUMIDITY", DEFAULT_TARGET_HUMIDITY)),
            "min_indoor_temp": int(os.getenv("MIN_INDOOR_TEMP", DEFAULT_MIN_INDOOR_TEMP)),
        }
    except (ValueError, TypeError) as e:
        raise RuntimeError("Error loading environment variables") from e

def initialize_dehumidifier_controller(email, password, debug, verbose):
    """Initializes the dehumidifier controller."""
    sha256_password = sha256(password.encode()).hexdigest()
    return DehumidifierController(
        email=email,
        password="",
        sha256password=sha256_password,
        debug=debug,
        verbose=verbose,
    )

def fetch_indoor_environment(shelly_ip):
    """Fetches indoor temperature and humidity from Shelly device."""
    return get_shelly_environment(shelly_ip)

def fetch_outdoor_environment(latitude, longitude, OPENWEATHER_API_KEY):
    """Fetches outdoor temperature and humidity from weather API."""
    return get_weather_data(latitude, longitude, OPENWEATHER_API_KEY)

def evaluate_humidity_control(
    indoor_temp, indoor_humidity, outdoor_temp, outdoor_humidity, dehumidifier, target_humidity, min_indoor_temp, humidity_difference
):
    """Evaluates whether to use the dehumidifier or recommend ventilation."""
    try:
        status = dehumidifier.get_status()
        if not status or "status" in status and status["status"] == "unavailable":
            print("Error: Unable to retrieve dehumidifier status. Skipping action.")
            return False

        # Relevante Statuswerte extrahieren
        is_on = status.get("_powerMode", 0) == 1  # 1 = eingeschaltet
        current_humidity = status.get("_humidity", None)
        set_humidity = status.get("_humidity_set", None)

        if current_humidity is None or set_humidity is None:
            print("Error: Missing humidity data from device status.")
            return False

    except Exception as e:
        print(f"Error retrieving dehumidifier status: {e}")
        return False

    # Berechnung der Außenluftfeuchtigkeit nach Erwärmung
    outside_humidity_after_heating = calculate_relative_humidity(outdoor_temp, outdoor_humidity, indoor_temp)
    if indoor_temp <= min_indoor_temp:
        print(f"Too cold for ventilation (Indoor Temp: {indoor_temp}°C).")
        if indoor_humidity > target_humidity:
            if not is_on:
                print("Turning on dehumidifier.")
                dehumidifier.turn_on(target_humidity)
            else:
                print("Dehumidifier is already on.")
        else:
            if is_on:
                print("Turning off dehumidifier.")
                dehumidifier.turn_off()
            else:
                print("Dehumidifier is already off.")
        return False
    elif outside_humidity_after_heating < indoor_humidity - humidity_difference:
        print(f"Ventilation recommended. Outdoor humidity could reduce indoor humidity from {indoor_humidity}% to {outside_humidity_after_heating:.2f}%.")
        if is_on:
            print("Turning off dehumidifier for ventilation.")
            dehumidifier.turn_off()
        return True
    else:
        print(f"Ventilation not recommended. Humidity difference insufficient.")
        if indoor_humidity > target_humidity:
            if not is_on:
                print("Turning on dehumidifier.")
                dehumidifier.turn_on(target_humidity)
            else:
                print("Dehumidifier is already on.")
        else:
            if is_on:
                print("Turning off dehumidifier.")
                dehumidifier.turn_off()
            else:
                print("Dehumidifier is already off.")
        return False

def main():
    try:
        config = load_environment_variables()
        dehumidifier = initialize_dehumidifier_controller(
            config["dehumidifier_email"],
            config["dehumidifier_password"],
            config["dehumidifier_debug_mode"],
            config["dehumidifier_verbose_mode"],
        )
        dehumidifier.login()
        print("Dehumidifier login successful.")
    except Exception as e:
        print(f"Initialization error: {e}")
        return

    last_lufting_time = None
    lufting_recommended = False

    while True:
        try:
            indoor_temp, indoor_humidity = fetch_indoor_environment(config["shelly_ip"])
            if indoor_temp is None or indoor_humidity is None:
                print("Error fetching indoor data.")
                time.sleep(WAIT_TIME_SECONDS)
                continue

            outdoor_temp, outdoor_humidity = fetch_outdoor_environment(
                config["latitude"], config["longitude"], config["OPENWEATHER_API_KEY"]
            )
            if outdoor_temp is None or outdoor_humidity is None:
                print("Error fetching outdoor data.")
                time.sleep(WAIT_TIME_SECONDS)
                continue

            lufting_recommended = evaluate_humidity_control(
                indoor_temp, indoor_humidity, outdoor_temp, outdoor_humidity,
                dehumidifier, config["target_humidity"], config["min_indoor_temp"], config["humidity_difference"]
            )

            if lufting_recommended and last_lufting_time and (time.time() - last_lufting_time) > 600:
                print("Ventilation recommended but not performed. Turning on dehumidifier.")
                dehumidifier.turn_on(config["target_humidity"])
                lufting_recommended = False

            last_lufting_time = time.time() if lufting_recommended else None
            time.sleep(WAIT_TIME_SECONDS)
        except Exception as e:
            print(f"Runtime error: {e}")
            time.sleep(WAIT_TIME_SECONDS)

if __name__ == "__main__":
    main()