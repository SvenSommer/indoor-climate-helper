from datetime import datetime
import os
import time
import logging
import threading
from modules.shelly_module import get_shelly_environment
from modules.weather_module import get_weather_data
from services.database_service import DatabaseService
from dotenv import load_dotenv

load_dotenv()
LOG_FILE = os.getenv("LOG_FILE", "app.log")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
LATITUDE = float(os.getenv("LATITUDE", 0.0))
LONGITUDE = float(os.getenv("LONGITUDE", 0.0))
LOCATION_NAME = os.getenv("LOCATION_NAME", "Potsdam")
INTERVAL_SECONDS_WEATHER = int(os.getenv("INTERVAL_SECONDS_WEATHER", 300))  # Default: 5 minutes
INTERVAL_SECONDS_SHELLY = int(os.getenv("INTERVAL_SECONDS_SHELLY", 60))  # Default: 1 minute

class WorkerThreads:
    def __init__(self):
        self.weather_thread = None
        self.shelly_thread = None
        self.dehumidifier_thread = None

    def start_threads(self):
         # Start Weather Thread
        if not self.weather_thread or not self.weather_thread.is_alive():
            self.weather_thread = threading.Thread(target=self.periodic_weather_update, daemon=True)
            self.weather_thread.start()
            logging.info("Weather thread started.")
        else:
            logging.info("Weather thread is already running. Skipping start.")

        # Start Shelly Thread
        if not self.shelly_thread or not self.shelly_thread.is_alive():
            self.shelly_thread = threading.Thread(target=self.periodic_shelly_update, daemon=True)
            self.shelly_thread.start()
            logging.info("Shelly thread started.")
        else:
            logging.info("Shelly thread is already running. Skipping start.")

        return

        # Start Dehumidifier Thread
        if not self.dehumidifier_thread or not self.dehumidifier_thread.is_alive():
            self.dehumidifier_thread = threading.Thread(target=self.periodic_dehumidifier_update, daemon=True)
            self.dehumidifier_thread.start()
            logging.info("Dehumidifier thread started.")
        else:
            logging.info("Dehumidifier thread is already running. Skipping start.")

    @staticmethod
    def initialize_dehumidifier(email, password):
        try:
            from modules.dehumidifier_module import DehumidifierController
            from hashlib import sha256

            sha256_password = sha256(password.encode()).hexdigest()

            dehumidifier = DehumidifierController(
                email=email,
                password="",
                sha256password=sha256_password,
                debug=os.getenv("DEHUMIDIFIER_DEBUG_MODE") == "True",
                verbose=os.getenv("DEHUMIDIFIER_VERBOSE_MODE") == "True",
            )
            dehumidifier.login()
            logging.info(f"Dehumidifier login successful for email {email}.")
            return dehumidifier
        except Exception as e:
            logging.error(f"Error initializing dehumidifier for email {email}: {e}")
            raise

    @staticmethod
    def periodic_weather_update():
        db_service = DatabaseService()  # Verbindung nur einmal öffnen
        try:
            while True:
                WorkerThreads.save_weather_data(db_service)
                time.sleep(INTERVAL_SECONDS_WEATHER)
        except Exception as e:
            logging.error(f"Error in periodic weather update: {e}")
        finally:
            db_service.close()

    @staticmethod
    def periodic_shelly_update():
        db_service = DatabaseService()  # Verbindung nur einmal öffnen
        try:
            while True:
                WorkerThreads.save_shelly_data(db_service)
                time.sleep(INTERVAL_SECONDS_SHELLY)
        except Exception as e:
            logging.error(f"Error in periodic Shelly update: {e}")
        finally:
            db_service.close()

    @staticmethod
    def periodic_dehumidifier_update():
        db_service = DatabaseService()
        try:
            while True:
                WorkerThreads.save_dehumidifier_data(db_service)
                time.sleep(INTERVAL_SECONDS_SHELLY)
        except Exception as e:
            logging.error(f"Error in periodic dehumidifier update: {e}")
        finally:
            db_service.close()

    @staticmethod
    def save_dehumidifier_data(db_service):
        try:
            logging.info("Saving dehumidifier data...")
            # Alle Dehumidifier-Geräte abrufen
            dehumidifier_devices = db_service.get_dehumidifier_devices()

            logging.info(f"Found {len(dehumidifier_devices)} dehumidifier devices in the database.")

            if not dehumidifier_devices:
                logging.warning("No dehumidifier devices found in the database.")
                return

            for device in dehumidifier_devices:
                # Initialisieren des Controllers für jedes Gerät
                logging.info(f"Initializing dehumidifier for device ID {device.id}...")
                logging.debug(f"Device: {device}")
                dehumidifier = WorkerThreads.initialize_dehumidifier(device.username, device.password)

                # Status abrufen und speichern
                status = dehumidifier.get_status()
                if not status:
                    logging.error(f"Failed to retrieve status for device ID {device.id}.")
                    continue

                indoor_humidity = status.get("_humidity", None)
                if indoor_humidity is not None:
                    db_service.save_measurement(device.room_id, None, indoor_humidity)
                    logging.info(f"Humidity data saved for device ID {device.id} (Humidity: {indoor_humidity}%).")
                else:
                    logging.warning(f"Humidity data missing for device ID {device.id}.")
        except Exception as e:
            logging.error(f"Error saving dehumidifier data: {e}")

    @staticmethod
    def save_weather_data(db_service):
        try:
            weather_data = get_weather_data(LATITUDE, LONGITUDE, OPENWEATHER_API_KEY)
            
            if not weather_data:
                logging.error("Weather data could not be retrieved.")
                return

            # Externen Raum aus der Datenbank abrufen
            location_name = weather_data.get("location_name")
            external_room = db_service.get_room_by_name(location_name)
            
            if not external_room:
                logging.error("External room not found. Weather data not saved.")
                return
            db_service.save_measurement(external_room.id, weather_data.get("temperature"), weather_data.get("humidity"))

            # Wetterdaten speichern
            weather_details = {
                "room_id": external_room.id,
                "temperature": weather_data.get("temperature"),
                "humidity": weather_data.get("humidity"),
                "weather_description": weather_data.get("weather_description"),
                "wind_speed": weather_data.get("wind_speed"),
                "wind_direction": weather_data.get("wind_direction"),
                "feels_like": weather_data.get("feels_like"),
                "pressure": weather_data.get("pressure"),
                "cloud_coverage": weather_data.get("cloud_coverage"),
                "visibility": weather_data.get("visibility"),
                "sunrise": datetime.utcfromtimestamp(weather_data.get("sunrise")) if weather_data.get("sunrise") else None,
                "sunset": datetime.utcfromtimestamp(weather_data.get("sunset")) if weather_data.get("sunset") else None,
            }

            # Wetterbericht speichern
            db_service.save_weather_report(**weather_details)

            logging.info("Weather data saved successfully.")
        
        except Exception as e:
            logging.error(f"Error saving weather data: {e}")

    @staticmethod
    def save_shelly_data(db_service):
        try:
            shelly_devices = db_service.get_shelly_devices()
            for device in shelly_devices:
                temperature, humidity = get_shelly_environment(device.ip)
                if temperature is not None and humidity is not None:
                    db_service.save_measurement(device.room_id, temperature, humidity)
                    logging.info(f"Shelly data saved for device '{device.name}' (IP: {device.ip}).")
                else:
                    logging.error(f"Failed to fetch data for Shelly device '{device.name}' (IP: {device.ip}).")
        except Exception as e:
            logging.error(f"Error saving Shelly data: {e}")