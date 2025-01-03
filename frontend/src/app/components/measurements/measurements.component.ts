import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { NgChartsModule } from 'ng2-charts'; // Importiere das NgChartsModule
import { ChartConfiguration } from 'chart.js';

@Component({
  selector: 'app-measurements',
  standalone: true,
  imports: [CommonModule, FormsModule, NgChartsModule], // Füge das NgChartsModule hinzu
  templateUrl: './measurements.component.html',
  styleUrls: ['./measurements.component.scss'],
})
export class MeasurementsComponent implements OnInit {
  measurements: any[] = [];
  roomId: number | null = null;
  roomName: string | null = null;
  reloadInterval: any;
  countdownInterval: any;
  reloadTime: number = 30; // Zeit zwischen Reloads (in Sekunden)
  countdown: number = this.reloadTime; // Countdown-Startwert

  // Chart-Properties
  chartData: ChartConfiguration['data'] = {
    datasets: [],
    labels: [],
  };

  chartOptions: ChartConfiguration['options'] = {
    responsive: true,
    plugins: {
      legend: {
        display: true,
        position: 'top',
      },
      tooltip: {
        enabled: true,
      },
    },
  };

  // Pagination & Sorting
  sorting: string = 'timestamp';
  order: 'asc' | 'desc' = 'desc';
  count: number = 10000;
  offset: number = 0;
  totalCount: number = 0;
  startDate: string | null = null;
  endDate: string | null = null;

  constructor(private apiService: ApiService, private route: ActivatedRoute, private router: Router) {}

  ngOnInit(): void {
    this.route.params.subscribe((params) => {
      this.roomId = +params['room_id'];
      this.loadRoomName();
      this.loadMeasurements();
    });

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
        this.loadMeasurements(); // Messungen neu laden
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

  loadRoomName(): void {
    if (!this.roomId) return;

    this.apiService.getRoomById(this.roomId).subscribe({
      next: (response) => {
        this.roomName = response.name; // Raumnamen setzen
      },
      error: (err) => {
        console.error('Fehler beim Abrufen des Raumnamens:', err);
      },
    });
  }

  loadMeasurements(): void {
    if (!this.roomId) return;

    this.apiService
      .getMeasurements(
        this.roomId,
        this.sorting,
        this.order,
        this.count,
        this.offset,
        this.startDate ?? undefined,
        this.endDate ?? undefined
      )
      .subscribe({
        next: (response) => {
          this.measurements = response.measurements || [];
          this.totalCount = response.totalCount || 0; // Gesamtanzahl der Messungen

          if (!this.startDate && response.firstDate) {
            this.startDate = response.firstDate.split('T')[0]; // Nur Datumsteil
          }
          if (!this.endDate && response.lastDate) {
            this.endDate = response.lastDate.split('T')[0]; // Nur Datumsteil
          }

          this.updateChartData(); // Chart aktualisieren
        },
        error: (err) => {
          console.error('Fehler beim Abrufen der Messungen:', err);
        },
      });
  }

  updateChartData(): void {
    // Labels und Daten für das Chart
    const labels = this.measurements
      .map((m) =>
        new Date(m.timestamp).toLocaleString('de-DE', {
          day: '2-digit',
          month: '2-digit',
          year: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
        })
      )
      .reverse(); // Reihenfolge der Labels umkehren

    const temperatureData = this.measurements
      .map((m) => m.temperature)
      .reverse(); // Reihenfolge der Temperaturdaten umkehren

    const humidityData = this.measurements
      .map((m) => m.humidity)
      .reverse(); // Reihenfolge der Luftfeuchtigkeitsdaten umkehren

    const potential_humidityData = this.measurements
      .map((m) => m.potential_humidity)
      .reverse(); // Reihenfolge der Luftfeuchtigkeitsdaten umkehren

    this.chartData = {
      labels, // Labels mit detailliertem Zeitstempel
      datasets: [
        {
          data: temperatureData,
          label: 'Temperatur (°C)',
          fill: false,
          borderColor: 'blue',
          tension: 0.1,
        },
        {
          data: humidityData,
          label: 'Luftfeuchtigkeit (%)',
          fill: false,
          borderColor: 'green',
          tension: 0.1,
        },
        {
          data: potential_humidityData,
          label: 'Potentielle Luftfeuchtigkeit (%)',
          fill: false,
          borderColor: 'yellow',
          tension: 0.1,
        },
      ],
    };
  }

  changeSorting(column: string): void {
    if (this.sorting === column) {
      this.order = this.order === 'asc' ? 'desc' : 'asc';
    } else {
      this.sorting = column;
      this.order = 'asc';
    }
    this.loadMeasurements();
  }

  changePage(next: boolean): void {
    if (next) {
      if (this.offset + this.count < this.totalCount) {
        this.offset += this.count;
        this.loadMeasurements();
      }
    } else {
      if (this.offset > 0) {
        this.offset = Math.max(this.offset - this.count, 0);
        this.loadMeasurements();
      }
    }
  }

  goBackToRooms(): void {
    this.router.navigate(['/rooms']); // Zurück zur /rooms-Seite
  }

  applyFilter(): void {
    this.offset = 0; // Reset Pagination
    this.loadMeasurements();
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
