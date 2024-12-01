# Luftfeuchtigkeitsanalyse & Lüftungshilfe

Ein Python-basiertes Tool zur Berechnung der relativen Luftfeuchtigkeit von Außenluft, wenn diese auf eine gegebene Innentemperatur erwärmt wird. Mit Hilfe von Wetterdaten einer API wird automatisch entschieden, ob Lüften sinnvoll ist.

## Features

- Berechnung der relativen Luftfeuchtigkeit nach Erwärmung
- Integration von Wetter-APIs (z. B. OpenWeatherMap) zur Abfrage der aktuellen Außentemperatur und relativen Luftfeuchtigkeit
- Visualisierung der Lüftungskurve (Außentemperatur vs. relative Luftfeuchtigkeit bei Innentemperatur)
- Anpassbare Parameter (Außentemperatur, relative Feuchtigkeit, Innentemperatur)

---

## Installation

### Voraussetzungen
- Python 3.8 oder höher
- Bibliotheken:
  - `requests`
  - `matplotlib`
  - `numpy`

### Installation der Abhängigkeiten
```bash
pip install -r requirements.txt
```

### API-Schlüssel erhalten:
- Registrieren Sie sich auf der OpenWeatherMap-Website https://openweathermap.org/ und erstellen Sie ein Konto, um einen API-Schlüssel zu erhalten.