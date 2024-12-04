import { Routes } from '@angular/router';
import { RoomsComponent } from './components/rooms/rooms.component';
import { MeasurementsComponent } from './components/measurements/measurements.component';

export const routes: Routes = [
  { path: 'rooms', component: RoomsComponent },
  { path: 'measurements/:room_id', component: MeasurementsComponent }, // Messungen für Räume
  { path: '', redirectTo: '/rooms', pathMatch: 'full' }, // Standardroute
  { path: '**', redirectTo: '/rooms' }, // Fallback-Route (ganz am Ende!)
];
