import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../services/api.service';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { RouterModule } from '@angular/router';



@Component({
  selector: 'app-rooms',
  standalone: true, // Standalone-Komponente
  imports: [CommonModule, FormsModule, FontAwesomeModule, RouterModule],
  templateUrl: './rooms.component.html',
  styleUrls: ['./rooms.component.scss'],
})
export class RoomsComponent implements OnInit {
  rooms: any[] = [];
  reloadInterval: any;
  countdownInterval: any;
  reloadTime: number = 30; // Zeit zwischen Reloads (in Sekunden)
  countdown: number = this.reloadTime; // Countdown-Startwert
  weatherData: any = null;
  expandedRoomId: number | null = null;
  showAddRoom: boolean = false; // Steuert das Formular für Raum hinzufügen
  editingRoomId: number | null = null; // Raum im Bearbeitungsmodus
  newRoomName: string = '';
  editRoomName: string = ''; // Neuer Name beim Bearbeiten
  showAddDevice: number | null = null; // Steuert das Formular für Geräte hinzufügen
  configRoomId: number | null = null
  newDevice: any = {
    name: '',
    room_id: null,
    device_type: '',
    ip: '',
    username: '',
    password: '',
  };

  selectedDehumidifierStatus: any = null;
  dehumidifierTargetHumidity: number = 50;

  constructor(private apiService: ApiService) { }

  ngOnInit(): void {
    this.loadRooms();
    this.startReloadCountdown();
  }

  ngOnDestroy(): void {
    this.stopIntervals();
  }

  startReloadCountdown(): void {
    // Countdown-Intervall für jede Sekunde
    this.countdown = this.reloadTime; // Countdown zurücksetzen
    this.countdownInterval = setInterval(() => {
      if (this.countdown > 0) {
        this.countdown--;
      } else {
        this.loadRooms();
        this.resetCountdown(); // Countdown zurücksetzen
      }
    }, 1000); // Jede Sekunde aktualisieren
  }

  resetCountdown(): void {
    this.countdown = this.reloadTime; // Countdown zurücksetzen
  }

  stopIntervals(): void {
    // Alle Intervalle aufräumen
    if (this.countdownInterval) {
      clearInterval(this.countdownInterval);
    }
  }

  loadRooms(): void {
    this.apiService.getRooms().subscribe({
      next: (response) => {
        this.rooms = response.rooms;
        this.weatherData = response.weather_data; // Wetterdaten speichern
      },
      error: (err) => {
        console.error('Fehler beim Abrufen der Räume:', err);
      },
    });
  }

  // Luftentfeuchter-Status abrufen
  getDehumidifierStatus(deviceId: number): void {
    this.apiService.getDehumidifierStatus(deviceId).subscribe({
      next: (status) => {
        this.selectedDehumidifierStatus = status;
        console.log('Luftentfeuchter-Status:', status);
      },
      error: (err) => {
        console.error('Fehler beim Abrufen des Luftentfeuchter-Status:', err);
      },
    });
  }

  hasDehumidifier(devices: any[]): boolean {
    return devices.some(device => device.device_type === 'Dehumidifier');
  }

  getDehumidifierId(devices: any[]): number | null {
    const dehumidifier = devices.find(device => device.device_type === 'Dehumidifier');
    return dehumidifier ? dehumidifier.id : null;
  }

  // Luftentfeuchter steuern
  controlDehumidifier(deviceId: number | null, action: 'on' | 'off'): void {
    if (deviceId === null) {
      console.error('Ungültige Geräte-ID für Steuerung.');
      return;
    }

    const targetHumidity = action === 'on' ? this.dehumidifierTargetHumidity : undefined;
    this.apiService.controlDehumidifier(deviceId, action, targetHumidity).subscribe({
      next: (response) => {
        console.log('Luftentfeuchter erfolgreich gesteuert:', response);
        this.getDehumidifierStatus(deviceId); // Aktualisierten Status abrufen
      },
      error: (err) => {
        console.error('Fehler bei der Steuerung des Luftentfeuchters:', err);
      },
    });
  }

  getTranslatedStatus(status: any): any {
    return {
      "Trocknen von Kleidung": status._dryClothesSetSwitch === 1 ? "Eingeschaltet" : "Ausgeschaltet",
      "Filterwechsel erforderlich": status._filterShow ? "Ja" : "Nein",
      "Aktuelle Luftfeuchtigkeit": `${status._humidity}%`,
      "Eingestellte Luftfeuchtigkeit": `${status._humidity_set}%`,
      "Ionisator": status._ionSetSwitch === 1 ? "Eingeschaltet" : "Ausgeschaltet",
      "Display aktiv": status._isDisplay ? "Ja" : "Nein",
      "Betriebsmodus": status._powerMode === 1 ? "Eingeschaltet" : "Ausgeschaltet",
      "Modus": this.getModeName(status._setMode),
      "Wassertank voll": status._tankShow ? "Ja" : "Nein",
      "Luftstrom (oben/unten)": status._upAndDownSwing === 1 ? "Aktiv" : "Inaktiv",
      "Windgeschwindigkeit": `${status._windSpeed}%`,
      "Timer zum Ausschalten": this.formatTimer(status.timingCloseHour, status.timingCloseMinute),
      "Timer zum Einschalten": this.formatTimer(status.timingOpenHour, status.timingOpenMinute),
    };
  }

  getTranslatedStatusArray(status: any): { key: string; value: string }[] {
    const translatedStatus = this.getTranslatedStatus(status);
    return Object.keys(translatedStatus).map((key) => ({
      key,
      value: translatedStatus[key],
    }));
  }

  getModeName(mode: number): string {
    const modes: { [key: number]: string } = {
      0: "Automatik",
      1: "Manuell",
      2: "Kleidung trocknen",
    };
    return modes[mode] || "Unbekannt";
  }

  formatTimer(hours: number, minutes: number): string {
    return hours > 0 || minutes > 0
      ? `${hours} Stunden, ${minutes} Minuten`
      : "Kein Timer gesetzt";
  }

  toggleRoomDetails(roomId: number): void {
    this.expandedRoomId = this.expandedRoomId === roomId ? null : roomId;
  }

  toggleAddRoom(): void {
    this.showAddRoom = !this.showAddRoom;
  }

  startEditingRoom(room: any): void {
    this.editingRoomId = room.id;
    this.editRoomName = room.name; // Aktuellen Namen laden
  }

  toggleAddDevice(roomId: number): void {
    this.showAddDevice = this.showAddDevice === roomId ? null : roomId;
    this.newDevice.room_id = roomId;
  }

  addRoom(): void {
    if (this.newRoomName.trim() === '') {
      alert('Raumname ist erforderlich!');
      return;
    }

    this.apiService.addRoom(this.newRoomName).subscribe({
      next: () => {
        this.newRoomName = '';
        this.showAddRoom = false; // Formular schließen
        this.loadRooms();
      },
      error: (err) => {
        console.error('Fehler beim Hinzufügen des Raums:', err);
      },
    });
  }

  saveRoomName(): void {
    if (this.editRoomName.trim() === '') {
      alert('Raumname darf nicht leer sein!');
      return;
    }

    console.log(`Updating room with ID: ${this.editingRoomId}, Name: ${this.editRoomName}`);
    this.apiService.updateRoom(this.editingRoomId!, this.editRoomName).subscribe({
      next: () => {
        console.log('Room updated successfully');


        this.loadRooms(); // Aktualisierte Räume laden
      },
      error: (err) => {
        console.error('Fehler beim Aktualisieren des Raums:', err);
      },
    });
  }

  deleteRoom(roomId: number): void {
    const confirmed = window.confirm('Möchten Sie diesen Raum wirklich löschen?');
    if (confirmed) {
      this.apiService.deleteRoom(roomId).subscribe({
        next: () => {
          this.loadRooms(); // Räume neu laden
        },
        error: (err) => {
          console.error('Fehler beim Löschen des Raums:', err);
        },
      });
    }
  }

  cancelEditing(roomId: number): void {
    this.editingRoomId = null;
    const room = this.rooms.find(r => r.id === roomId);
    if (room) {
      this.editRoomName = room.name; // Namen initialisieren
    }
  }

  addDevice(): void {
    if (!this.newDevice.room_id) {
      alert('Raum-ID ist erforderlich!');
      return;
    }

    this.apiService.addDevice(this.newDevice).subscribe({
      next: () => {
        this.newDevice = {
          name: '',
          room_id: null,
          device_type: '',
          ip: '',
          username: '',
          password: '',
        };
        this.showAddDevice = null; // Formular schließen
        this.loadRooms();
      },
      error: (err) => {
        console.error('Fehler beim Hinzufügen des Geräts:', err);
      },
    });
  }

  deleteDevice(deviceId: number): void {
    const confirmed = window.confirm('Möchten Sie dieses Gerät wirklich löschen?');
    if (confirmed) {
      this.apiService.deleteDevice(deviceId).subscribe({
        next: () => {
          this.loadRooms();
        },
        error: (err) => {
          console.error('Fehler beim Löschen des Geräts:', err);
        },
      });
    }
  }

  toggleConfig(roomId: number): void {
    if (this.configRoomId === roomId) {
      this.configRoomId = null;
      this.editingRoomId = null; // ID zurücksetzen
    } else {
      this.configRoomId = roomId;
      this.editingRoomId = roomId; // ID setzen
      const room = this.rooms.find(r => r.id === roomId);
      if (room) {
        this.editRoomName = room.name; // Namen initialisieren
      }
    }
  }
  calculateTimeSince(timestamp: string | null): string {
    if (!timestamp) {
      return 'Keine Messung verfügbar';
    }

    const now = new Date().getTime();
    const measurementTime = new Date(timestamp).getTime();

    // Zeitverschiebung: 60 Minuten in Millisekunden
    const adjustedTime = measurementTime + 60 * 60 * 1000;

    const diffInSeconds = Math.floor((now - adjustedTime) / 1000);

    if (diffInSeconds < 60) {
      return 'Gerade eben';
    } else if (diffInSeconds < 3600) {
      const minutes = Math.floor(diffInSeconds / 60);
      return `vor ${minutes} ${minutes === 1 ? 'Minute' : 'Minuten'}`;
    } else if (diffInSeconds < 86400) {
      const hours = Math.floor(diffInSeconds / 3600);
      const timeString = new Date(adjustedTime).toLocaleTimeString('de-DE', {
        hour: '2-digit',
        minute: '2-digit',
      });
      return `vor über ${hours} ${hours === 1 ? 'Stunde' : 'Stunden'} (${timeString})`;
    } else {
      const days = Math.floor(diffInSeconds / 86400);
      const dateString = new Date(adjustedTime).toLocaleDateString('de-DE', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
      });
      const timeString = new Date(adjustedTime).toLocaleTimeString('de-DE', {
        hour: '2-digit',
        minute: '2-digit',
      });
      return `vor über ${days} ${days === 1 ? 'Tag' : 'Tagen'} (${dateString}, ${timeString})`;
    }
  }

  calculateTimeUntil(timestamp: string | null): string {
    if (!timestamp) {
      return 'Keine Zeit verfügbar';
    }

    const now = new Date().getTime();
    const targetTime = new Date(timestamp).getTime();

    // Zeitdifferenz in Sekunden berechnen
    const diffInSeconds = Math.floor((targetTime - now) / 1000);

    if (diffInSeconds < 0) {
      return 'Zeitpunkt überschritten';
    } else if (diffInSeconds < 60) {
      return 'In weniger als einer Minute';
    } else if (diffInSeconds < 3600) {
      const minutes = Math.floor(diffInSeconds / 60);
      return `In ${minutes} ${minutes === 1 ? 'Minute' : 'Minuten'}`;
    } else if (diffInSeconds < 86400) {
      const hours = Math.floor(diffInSeconds / 3600);
      const timeString = new Date(targetTime).toLocaleTimeString('de-DE', {
        hour: '2-digit',
        minute: '2-digit',
      });
      return `In über ${hours} ${hours === 1 ? 'Stunde' : 'Stunden'} (${timeString})`;
    } else {
      const days = Math.floor(diffInSeconds / 86400);
      const dateString = new Date(targetTime).toLocaleDateString('de-DE', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
      });
      const timeString = new Date(targetTime).toLocaleTimeString('de-DE', {
        hour: '2-digit',
        minute: '2-digit',
      });
      return `In über ${days} ${days === 1 ? 'Tag' : 'Tagen'} (${dateString}, ${timeString})`;
    }
  }

  getRecommendation(measurement: { temperature: number; humidity: number; potential_humidity: number }): string {
    const temp = measurement.temperature;
    const humidity = measurement.humidity;
    const potentialHumidity = measurement.potential_humidity;

    if (humidity && potentialHumidity) {
      const humidityDiff = Math.abs(humidity - potentialHumidity);

      // Lüften beenden, wenn die Temperatur unter 21°C fällt oder die Differenz unter 2% ist
      if (temp < 21 || humidityDiff <= 2) {
        return 'Lüften beenden';
      }

      // Lüften empfehlen, wenn die Differenz größer als 10% ist
      if (humidityDiff > 10) {
        return 'Lüften';
      }
    }

    // Keine Empfehlung
    return '-';
  }
}
