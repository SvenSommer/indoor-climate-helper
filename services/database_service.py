from datetime import datetime
from modules.database_setup import Device, Room, Measurement, SessionLocal
from sqlalchemy import func

class DatabaseService:
    def __init__(self):
        self.db = SessionLocal()

    def close(self):
        self.db.close()

    def get_shelly_devices(self):
        return self.db.query(Device).filter(Device.device_type == "Shelly").all()

    def save_measurement(self, room_id, temperature, humidity):
        try:
            # Prüfen, ob ein Messpunkt mit ähnlichem Zeitstempel, Temperatur und Feuchtigkeit existiert
            existing_measurement = self.db.query(Measurement).filter(
                Measurement.room_id == room_id,
                func.abs(func.unix_timestamp(Measurement.timestamp) - func.unix_timestamp(datetime.utcnow())) < 5,  # Prüft auf Zeitstempel-Differenz kleiner als 5 Sekunden
                Measurement.temperature == temperature,
                Measurement.humidity == humidity
            ).first()

            # Wenn kein ähnlicher Messpunkt vorhanden ist, speichern
            if not existing_measurement:
                new_measurement = Measurement(
                    room_id=room_id,
                    timestamp=datetime.utcnow(),
                    temperature=temperature,
                    humidity=humidity,
                )
                self.db.add(new_measurement)
                self.db.commit()

        except Exception as e:
            self.db.rollback()
            raise e

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

    def get_all_measurements(self, room_id, sorting="timestamp", order="asc", count=None, offset=0):
        query = self.db.query(Measurement).filter_by(room_id=room_id)
        query = query.order_by(getattr(Measurement, sorting).asc() if order == "asc" else getattr(Measurement, sorting).desc())
        if offset:
            query = query.offset(offset)
        if count:
            query = query.limit(count)
        return query.all()