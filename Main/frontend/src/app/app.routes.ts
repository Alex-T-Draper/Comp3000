import { Routes } from '@angular/router';
import { TosViewerComponent } from './components/tos-viewer/tos-viewer';

export const routes: Routes = [
  { path: '', redirectTo: 'tos', pathMatch: 'full' },
  { path: 'tos', component: TosViewerComponent }
];
