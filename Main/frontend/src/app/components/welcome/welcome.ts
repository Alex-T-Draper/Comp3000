// src/app/components/welcome/welcome.ts
import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-welcome',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './welcome.html',
  styleUrls: ['./welcome.scss']
})
export class WelcomeComponent {
  userName: string = '';
  isLoading: boolean = false;
  error: string | null = null;
  
  private apiUrl = 'http://127.0.0.1:8000/api';

  constructor(
    private router: Router,
    private http: HttpClient
  ) {}

  /**
   * Validate and start the study
   */
  startStudy(): void {
    // Validate name
    if (!this.userName || this.userName.trim().length === 0) {
      this.error = 'Please enter your name to continue.';
      return;
    }

    if (this.userName.trim().length < 2) {
      this.error = 'Name must be at least 2 characters.';
      return;
    }

    this.isLoading = true;
    this.error = null;

    // Create/get user in database
    this.http.post(`${this.apiUrl}/users`, { name: this.userName.trim() })
      .subscribe({
        next: (response: any) => {
          // Store user name in session storage for use in ToS viewer
          sessionStorage.setItem('userName', this.userName.trim());
          sessionStorage.setItem('userId', response.userId);
          
          // Navigate to ToS viewer
          this.router.navigate(['/tos-plain']);
        },
        error: (err) => {
          console.error('Error creating user:', err);
          this.error = 'Failed to start study. Please try again.';
          this.isLoading = false;
        }
      });
  }

  /**
   * Handle Enter key press
   */
  onKeyPress(event: KeyboardEvent): void {
    if (event.key === 'Enter') {
      this.startStudy();
    }
  }
}