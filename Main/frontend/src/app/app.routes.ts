// src/app/app.routes.ts
import { Routes } from '@angular/router';
import { WelcomeComponent } from './components/welcome/welcome';
import { TosAiEnhancedComponent } from './components/tos-ai-enhanced/tos-ai-enhanced';
import { TosPlainComponent } from './components/tos-plain/tos-plain';
import { TosScrollRequiredComponent } from './components/tos-scroll-required/tos-scroll-required';
import { TosFormattedComponent } from './components/tos-formatted/tos-formatted';

export const routes: Routes = [
  { path: '', component: WelcomeComponent },
  { path: 'tos', component: TosAiEnhancedComponent }, 
  { path: 'tos-plain', component: TosPlainComponent },
  { path: 'tos-scroll-required', component: TosScrollRequiredComponent },
  { path: 'tos-formatted', component: TosFormattedComponent },
  { path: '**', redirectTo: '' }
];