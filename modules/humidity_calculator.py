import numpy as np
import matplotlib.pyplot as plt
import logging

# Logging konfigurieren
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

def max_absolute_humidity(temp):
    """
    Calculates the maximum absolute humidity in g/m³ for a given temperature in °C.
    """
    try:
        humidity = 6.112 * np.exp((17.67 * temp) / (temp + 243.5)) * 2.1674 / (273.15 + temp)
        #logging.debug(f"Maximale absolute Feuchtigkeit bei {temp}°C: {humidity:.2f} g/m³")
        return humidity
    except Exception as e:
        logging.error(f"Fehler bei der Berechnung der maximalen absoluten Feuchtigkeit: {e}")
        return 0

def calculate_relative_humidity(out_temp, out_humidity, in_temp, delta_t=-2):
    """
    Calculates the relative humidity of outdoor air when heated to indoor temperature.
    """
    try:
        in_temp += delta_t  # descease indoor temperature by delta_t, because it will cool down, when ventilated
        abs_humidity_out = max_absolute_humidity(out_temp) * (out_humidity / 100)
        abs_humidity_in_max = max_absolute_humidity(in_temp)
        if abs_humidity_in_max == 0:
            logging.warning("Maximale absolute Feuchtigkeit für die Innentemperatur ist 0. Division vermieden.")
            return 0
        relative_humidity_in = (abs_humidity_out / abs_humidity_in_max) * 100
        #logging.debug(f"Relative Feuchtigkeit bei {out_temp}°C außen und {in_temp}°C innen: {relative_humidity_in:.2f}%")
        return relative_humidity_in
    except Exception as e:
        logging.error(f"Fehler bei der Berechnung der relativen Feuchtigkeit: {e}")
        return 0

def plot_humidity_curve(out_temp, out_humidity, in_temp):
    """
    Plots the relative humidity curve of outdoor air when heated to indoor temperature.
    """
    try:
        temperatures = np.linspace(-10, 30, 100)  # Outdoor temperature range
        relative_humidities = [
            calculate_relative_humidity(temp, out_humidity, in_temp) for temp in temperatures
        ]
        
        # Current value for the given outdoor temperature
        current_relative_humidity = calculate_relative_humidity(out_temp, out_humidity, in_temp)

        # Plot the graph
        plt.figure(figsize=(10, 6))
        plt.plot(temperatures, relative_humidities, label="Relative Luftfeuchtigkeit bei Erwärmung")
        plt.axvline(out_temp, color="red", linestyle="--", label=f"Aktuelle Außentemperatur: {out_temp}°C")
        plt.axhline(current_relative_humidity, color="blue", linestyle="--",
                    label=f"Relative Luftfeuchtigkeit bei {in_temp}°C: {current_relative_humidity:.2f}%")
        plt.title("Relative Luftfeuchtigkeit der Außenluft nach Erwärmung auf Innentemperatur", fontsize=14)
        plt.xlabel("Außentemperatur (°C)", fontsize=12)
        plt.ylabel("Relative Luftfeuchtigkeit bei Innentemperatur (%)", fontsize=12)
        plt.legend()
        plt.grid(True)
        plt.show()
    except Exception as e:
        logging.error(f"Fehler beim Plotten der Luftfeuchtigkeitskurve: {e}")
