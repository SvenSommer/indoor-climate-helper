from datetime import datetime, timedelta
from modules.database_setup import Device, Room, Measurement, SessionLocal, WeatherReport
from modules.humidity_calculator import calculate_relative_humidity
from sqlalchemy import func
import logging
from pytz import timezone


logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
class DatabaseService:
    def __init__(self):
        self.db = SessionLocal()

    def close(self):
        self.db.close()

    def get_shelly_devices(self):
        return self.db.query(Device).filter(Device.device_type == "Shelly").all()
    
    def get_dehumidifier_devices(self):
        return self.db.query(Device).filter(Device.device_type == "Dehumidifier").all()

    def save_measurement(self, room_id, temperature, humidity):
        """
        Speichert eine neue Messung, wenn sie sich von der letzten unterscheidet, und berechnet die potenzielle Luftfeuchtigkeit.
        """
        try:
            # Letzten gespeicherten Messpunkt für den Raum abrufen
            last_measurement = (
                self.db.query(Measurement)
                .filter(Measurement.room_id == room_id)
                .order_by(Measurement.timestamp.desc())
                .first()
            )

            # Nur speichern, wenn sich der neue Messpunkt unterscheidet
            if not last_measurement or (
                last_measurement.temperature != temperature
                or last_measurement.humidity != humidity
            ):
                potential_humidity = self.calculate_potential_humidity(room_id, temperature)

                # Neuen Messpunkt speichern
                new_measurement = Measurement(
                    room_id=room_id,
                    timestamp=datetime.utcnow(),
                    temperature=temperature,
                    humidity=humidity,
                    potential_humidity=potential_humidity,
                )
                self.db.add(new_measurement)
                self.db.commit()
                logging.info(f"Messung für Raum {room_id} erfolgreich gespeichert.")
            else:
                logging.info(f"Keine Änderung erkannt. Messpunkt nicht gespeichert.")

        except Exception as e:
            self.db.rollback()
            logging.error(f"Fehler beim Speichern des Messwerts: {e}")
            raise e
            
    def update_potential_humidity_in_historical_data_with_logging(self, t_delta=-1):
        """
        Aktualisiert die potenzielle Luftfeuchtigkeit in historischen Messpunkten und gibt Fortschrittsnachrichten zurück.
        """
        try:
            # Gesamtanzahl der zu aktualisierenden Messpunkte abrufen
            total_count = self.db.query(Measurement).filter(
                Measurement.room_id != 1,
                Measurement.temperature.isnot(None)
            ).count()

            yield f"Starting update for {total_count} measurements...\n"
            measurements = (
                self.db.query(Measurement)
                .filter(
                    Measurement.room_id != 1,
                    Measurement.temperature.isnot(None)
                )
                .order_by(Measurement.timestamp.asc())
            )

            updated_count = 0

            for index, measurement in enumerate(measurements, start=1):
                try:
                    potential_humidity = self.calculate_potential_humidity(
                        measurement.room_id, measurement.temperature, measurement.timestamp, t_delta
                    )
                    if potential_humidity is not None:
                        measurement.potential_humidity = potential_humidity
                        self.db.flush()
                        updated_count += 1

                except Exception as measurement_error:
                    logging.error(f"Error processing measurement ID {measurement.id}: {measurement_error}")

            self.db.commit()
            yield f"Update completed: {updated_count}/{total_count} measurements updated successfully.\n"

        except Exception as e:
            self.db.rollback()
            logging.error(f"Error during update: {e}")
            yield f"Error: {e}\n"

    def save_weather_report(self, **weather_details):
        """
        Speichert Wetterdaten in der WeatherReport-Tabelle, falls keine ähnlichen Daten existieren.
        :param weather_details: Dictionary mit Wetterinformationen
        """
        try:
            # Prüfen, ob bereits ein ähnlicher Eintrag existiert (zeitnah und gleiche Raum-ID)
            existing_report = self.db.query(WeatherReport).filter(
                WeatherReport.room_id == weather_details["room_id"],
                func.abs(func.unix_timestamp(WeatherReport.timestamp) - func.unix_timestamp(datetime.utcnow())) < 5,
                WeatherReport.temperature == weather_details.get("temperature"),
                WeatherReport.humidity == weather_details.get("humidity"),
            ).first()

            if not existing_report:
                # Neuen Wetterbericht speichern
                weather_report = WeatherReport(**weather_details)
                self.db.add(weather_report)
                self.db.commit()
                logging.info("Weather report saved successfully.")
            else:
                logging.debug("Similar weather report already exists. No new entry created.")

        except Exception as e:
            self.db.rollback()
            logging.error(f"Error saving weather report: {e}")
            raise e
        
    def get_last_weather_report_for_room(self, room_id):
        """
        Holt den letzten Wetterbericht für einen bestimmten Raum.
        """
        try:
            return (
                self.db.query(WeatherReport)
                .filter_by(room_id=room_id)
                .order_by(WeatherReport.timestamp.desc())
                .first()
            )
        except Exception as e:
            logging.error(f"Error retrieving last weather report for room {room_id}: {e}")
            return None

    def get_room_by_id(self, id):
        return self.db.query(Room).filter_by(id=id).first()
    
    def get_room_by_name(self, name):
        return self.db.query(Room).filter_by(name=name).first()

    def get_all_rooms(self):
        return self.db.query(Room).order_by(Room.id.asc()).all()

    def add_room(self, name):
        try:
            new_room = Room(name=name)
            self.db.add(new_room)
            self.db.commit()
            return new_room
        except Exception as e:
            self.db.rollback()
            raise e

    def delete_room(self, room_id):
        try:
            room = self.db.query(Room).filter_by(id=room_id).first()
            if room:
                self.db.delete(room)
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            raise e

    def get_room_devices(self, room_id):
        return self.db.query(Device).filter_by(room_id=room_id).all()

    def get_last_measurement_for_room(self, room_id):
        return (
            self.db.query(Measurement)
            .filter_by(room_id=room_id)
            .order_by(Measurement.timestamp.desc())
            .first()
        )
    

    def get_measurements_for_room(self, room_id, start_time, end_time):
        """
        Holt alle Messwerte für einen bestimmten Raum im angegebenen Zeitraum.
        """
        try:
            # Konvertiere die Zeiten in UTC für die Abfrage
            start_time = start_time.astimezone(timezone('UTC'))
            end_time = end_time.astimezone(timezone('UTC'))

            logging.debug(f"Querying measurements for room {room_id} between {start_time} and {end_time}")

            return (
                self.db.query(Measurement)
                .filter(Measurement.room_id == room_id)
                .filter(Measurement.timestamp >= start_time)
                .filter(Measurement.timestamp <= end_time)
                .order_by(Measurement.timestamp)
                .all()
            )
        except Exception as e:
            logging.error(f"Error retrieving measurements for room {room_id}: {e}")
            return []
        
    def get_nearest_measurement(self, room_id, timestamp):
        """
        Findet den nächstgelegenen Messpunkt (vor oder nach einem gegebenen Zeitstempel).
        """
        before_measurement = (
            self.db.query(Measurement)
            .filter(
                Measurement.room_id == room_id,
                Measurement.timestamp <= timestamp
            )
            .order_by(Measurement.timestamp.desc())
            .first()
        )

        after_measurement = (
            self.db.query(Measurement)
            .filter(
                Measurement.room_id == room_id,
                Measurement.timestamp > timestamp
            )
            .order_by(Measurement.timestamp.asc())
            .first()
        )

        if before_measurement and after_measurement:
            delta_before = abs((timestamp - before_measurement.timestamp).total_seconds())
            delta_after = abs((after_measurement.timestamp - timestamp).total_seconds())
            return before_measurement if delta_before <= delta_after else after_measurement

        return before_measurement or after_measurement

    def get_all_measurements(self, room_id, sorting="timestamp", order="asc", count=None, offset=0):
        query = self.db.query(Measurement).filter_by(room_id=room_id)
        query = query.order_by(getattr(Measurement, sorting).asc() if order == "asc" else getattr(Measurement, sorting).desc())
        if offset:
            query = query.offset(offset)
        if count:
            query = query.limit(count)
        return query.all()
