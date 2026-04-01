// src/app/components/welcome/welcome.ts
import { Component, ViewChild, ElementRef, AfterViewInit, ChangeDetectorRef } from '@angular/core';
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
export class WelcomeComponent implements AfterViewInit {
  @ViewChild('userNameInput') userNameInput?: ElementRef<HTMLInputElement>;

  userName: string = '';
  isLoading: boolean = false;
  error: string | null = null;
  
  private apiUrl = 'http://127.0.0.1:8000/api';

  constructor(
    private router: Router,
    private http: HttpClient,
    private cdr: ChangeDetectorRef
  ) {}

  ngAfterViewInit() {
    // ViewChild is ready
  }

  // Validate and start the study
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

    // Create user in database
    this.http.post(`${this.apiUrl}/users`, { name: this.userName.trim() })
      .subscribe({
        next: (response: any) => {
          // Store user name in session storage
          sessionStorage.setItem('userName', this.userName.trim());
          sessionStorage.setItem('userId', response.userId);
          
          // Navigate to first condition
          this.router.navigate(['/tos-plain']);
        },
        error: (err) => {
          console.error('Error creating user:', err);
          
          // ALWAYS re-enable the form
          this.isLoading = false;
          
          // Force Angular to detect the change
          this.cdr.detectChanges();
          
          // Check for duplicate name error
          if (err?.status === 400 && err?.error?.detail?.includes('already exists')) {
            this.error = 'This name is already taken. Please choose a different name.';
            this.userName = ''; // Clear the input
            
            // Force another change detection after clearing
            this.cdr.detectChanges();
            
            // Focus input after a brief delay
            setTimeout(() => {
              const input = this.userNameInput?.nativeElement;
              if (input) {
                input.focus();
              }
            }, 100);
          } else if (err?.error?.detail) {
            this.error = err.error.detail;
          } else {
            this.error = 'Failed to start study. Please try again.';
          }
        }
      });
  }

  // Handle Enter key press
  onKeyPress(event: KeyboardEvent): void {
    if (event.key === 'Enter') {
      this.startStudy();
    }
  }
}