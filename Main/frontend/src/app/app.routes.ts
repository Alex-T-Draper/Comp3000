// src/app/app.routes.ts
import { Routes } from '@angular/router';
import { WelcomeComponent } from './components/welcome/welcome';
import { TosViewerComponent } from './components/tos-viewer/tos-viewer';

export const routes: Routes = [
  { path: '', component: WelcomeComponent }, 
  { path: 'tos', component: TosViewerComponent },  
  { path: '**', redirectTo: '' }  
];