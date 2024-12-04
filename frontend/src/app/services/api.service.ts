import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class ApiService {
  private apiUrl = 'http://192.168.178.27:5042';

  constructor(private http: HttpClient) { }

  getRooms(): Observable<any> {
    return this.http.get(`${this.apiUrl}/rooms`);
  }

  getRoomById(roomId: number): Observable<any> {
    return this.http.get(`${this.apiUrl}/rooms/${roomId}`);
  }

  addRoom(name: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/rooms`, { name });
  }

  // Raum aktualisieren
  updateRoom(roomId: number, name: string): Observable<any> {
    return this.http.put(`${this.apiUrl}/rooms/${roomId}`, { name });
  }

  // Raum löschen
  deleteRoom(roomId: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/rooms/${roomId}`);
  }

  // Geräte abrufen
  getDevices(): Observable<any> {
    return this.http.get(`${this.apiUrl}/devices`);
  }

  // Gerät hinzufügen
  addDevice(device: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/devices`, device);
  }

  // Gerät aktualisieren
  updateDevice(deviceId: number, device: any): Observable<any> {
    return this.http.put(`${this.apiUrl}/devices/${deviceId}`, device);
  }

  // Gerät löschen
  deleteDevice(deviceId: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/devices/${deviceId}`);
  }

  getMeasurements(
    roomId: number,
    sorting?: string,
    order?: 'asc' | 'desc',
    count?: number,
    offset?: number,
    startDate?: string,
    endDate?: string
  ): Observable<any> {
    const params: any = {};
    if (sorting) params.sorting = sorting;
    if (order) params.order = order;
    if (count) params.count = count;
    if (offset) params.offset = offset;

    // Backend erwartet "start_date" und "end_date"
    if (startDate) params.start_date = startDate; // Korrekte Benennung
    if (endDate) params.end_date = endDate; // Korrekte Benennung

    return this.http.get(`${this.apiUrl}/measurements/${roomId}`, { params });
  }

  // Luftentfeuchter-Status abrufen
  getDehumidifierStatus(deviceId: number): Observable<any> {
    return this.http.get(`${this.apiUrl}/dehumidifier/${deviceId}/status`);
  }

  // Luftentfeuchter steuern
  controlDehumidifier(deviceId: number, action: 'on' | 'off', targetHumidity?: number): Observable<any> {
    const payload: any = { action };
    if (action === 'on' && targetHumidity !== undefined) {
      payload.target_humidity = targetHumidity;
    }
    return this.http.post(`${this.apiUrl}/dehumidifier/${deviceId}/control`, payload);
  }

}


