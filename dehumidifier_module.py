import time
from midea_inventor_lib import MideaClient

class DehumidifierController:
    def __init__(self, email, password, sha256password, debug=False, verbose=False):
        self.client = MideaClient(email, password, sha256password, debug, verbose)
        self.device_id = None

    def login(self):
        """Melde dich an und hole die Geräte-ID."""
        res = self.client.login()
        if res == -1:
            raise Exception("Login error: please check credentials and logs.")
        self.device_id = self.get_device_id()

    def get_device_id(self):
        """Hole die Geräte-ID des ersten gefundenen Luftentfeuchters."""
        appliances = self.client.listAppliances()
        if not appliances:
            raise Exception("No appliances found.")
        # Annahme: Der erste Luftentfeuchter in der Liste wird verwendet
        return appliances[0]["id"]

    def turn_on(self, target_humidity):
        """Schalte den Luftentfeuchter ein und setze die Ziel-Luftfeuchtigkeit."""
        if self.device_id:
            self.client.send_poweron_command(self.device_id)
            self.client.send_target_humidity_command(self.device_id, target_humidity)

    def turn_off(self):
        """Schalte den Luftentfeuchter aus."""
        if self.device_id:
            self.client.send_poweroff_command(self.device_id)

    def parse_value(self, value):
        """
        Konvertiert Werte in das passende Python-Format.
        """
        if value.isdigit():
            return int(value)
        elif value.lower() in ["true", "false"]:
            return value.lower() == "true"
        elif "." in value:
            try:
                return float(value)
            except ValueError:
                return value  # Fallback zu String
        else:
            return value  # Standard: String
            
    def parse_status_string(self, status_string):
        """
        Parst den Status-String in ein Dictionary.
        Akzeptiert Status-Strings auch ohne Klammern oder mit unerwarteten Formaten.
        Beispiel-Input: 'DeHumidification [powerMode=0, mode=4, ...]'
        """
        try:
            # Finde den Start der Key-Value-Paare (nach dem ersten Leerzeichen)
            key_value_part = status_string.split(' ', 1)[1] if ' ' in status_string else status_string

            # Entferne Klammern, falls vorhanden
            key_value_part = key_value_part.strip('[]')

            # Teile die Parameter durch Kommas und setze sie in ein Dictionary
            status_dict = {}
            for item in key_value_part.split(','):
                key_value = item.split('=')
                if len(key_value) == 2:  # Validiert, dass es genau ein `=` gibt
                    key, value = key_value
                    status_dict[key.strip()] = self.parse_value(value.strip())
            return status_dict
        except Exception as e:
            raise ValueError(f"Failed to parse status string: {e}")



    def get_status(self):
        """
        Hole den Status des Luftentfeuchters.
        Gibt ein Dictionary mit dem Status zurück oder None bei Fehler.
        """
        if not self.device_id:
            raise Exception("Device ID not set. Login might have failed.")
        
        res = self.client.get_device_status(self.device_id)
        if res != 1:
            print("Failed to fetch device status.")
            return None

        # Zugriff auf den Gerätestatus
        status = self.client.deviceStatus
        if status:
            try:
                # Prüfen, ob `status` ein Objekt ist
                if hasattr(status, "to_dict"):
                    # Falls das Objekt eine `to_dict`-Methode hat, diese verwenden
                    parsed_status = status.to_dict()
                elif hasattr(status, "__dict__"):
                    # Andernfalls die Attribute des Objekts als Dictionary zurückgeben
                    parsed_status = vars(status)
                else:
                    # Andernfalls das Objekt als String darstellen und parsen
                    status_string = str(status)
                    print(f"DEBUG: Raw status string: {status_string}")
                    parsed_status = self.parse_status_string(status_string)

                print(f"DEBUG: Parsed status: {parsed_status}")
                return parsed_status
            except Exception as e:
                print(f"Error parsing status: {e}. Returning raw status.")
                return {"status_raw": str(status)}
        else:
            print("Status unavailable.")
            return {"status": "unavailable"}