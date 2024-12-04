import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-measurements',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './measurements.component.html',
  styleUrls: ['./measurements.component.scss'],
})
export class MeasurementsComponent implements OnInit {
  measurements: any[] = [];
  roomId: number | null = null;
  roomName: string | null = null;

  // Pagination & Sorting
  sorting: string = 'timestamp';
  order: 'asc' | 'desc' = 'desc';
  count: number = 10;
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
        },
        error: (err) => {
          console.error('Fehler beim Abrufen der Messungen:', err);
        },
      });
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
      // Weiter - Erhöhe den Offset, solange es mehr Ergebnisse gibt
      if (this.offset + this.count < this.totalCount) {
        this.offset += this.count;
        this.loadMeasurements();
      }
    } else {
      // Zurück - Verringere den Offset, solange er >= 0 bleibt
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
}
