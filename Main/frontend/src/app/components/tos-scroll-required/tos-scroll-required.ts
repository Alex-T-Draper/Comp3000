// src/app/components/tos-scroll-required/tos-scroll-required.ts
import { Component, OnInit, OnDestroy, ViewChild, ElementRef, HostListener, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { TrackingService } from '../../services/tracking';
import { NlpApiService } from '../../services/nlp-api';

@Component({
  selector: 'app-tos-scroll-required',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './tos-scroll-required.html',
  styleUrls: ['./tos-scroll-required.scss']
})
export class TosScrollRequiredComponent implements OnInit, OnDestroy {
  @ViewChild('tosContainer', { static: false }) tosContainer!: ElementRef;

  // ToS content
  tosText: string = '';
  tosTitle: string = '';
  tosId: string = 'scroll-required-tos-002';

  // Tracking
  userId: string = '';
  scrollDepth: number = 0;
  hasScrolledToBottom: boolean = false;

  constructor(
    private tracking: TrackingService,
    private router: Router,
    private nlpApi: NlpApiService,
    private cdr: ChangeDetectorRef
  ) {
    // Get user name from session storage
    this.userId = sessionStorage.getItem('userName') || 'anonymous';
  }

  ngOnInit(): void {
    // Always scroll to top when component loads
    window.scrollTo(0, 0);
    this.loadTosDocument();
  }

  ngOnDestroy(): void {
    this.tracking.endSession();
  }

  /**
   * Load the ToS document
   */
  loadTosDocument(): void {
    this.tosTitle = 'VaultDrive Terms of Service';
    this.tosId = 'scroll-required-tos-002';

    this.nlpApi.loadTosFile('cloudstorage_tos').subscribe({
      next: (text: string) => {
        this.tosText = text;
        this.initializeTracking();
        this.cdr.detectChanges();
      },
      error: (err: any) => {
        console.error('Error loading ToS document:', err);
        this.tosText = 'Failed to load Terms of Service. Please try again later.';
      }
    });
  }

  /**
   * Initialize tracking session
   */
  initializeTracking(): void {
    this.tracking.startSession(
      this.userId,
      this.tosId,
      this.tosText,
      this.tosTitle,
      'scroll-gate' // Condition type
    );
  }

  /**
   * Handle scroll events for tracking
   */
  @HostListener('window:scroll')
  onScroll(): void {
    const element = this.tosContainer?.nativeElement;
    if (!element) return;

    const windowHeight = window.innerHeight;
    const documentHeight = document.documentElement.scrollHeight;
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    
    // Calculate scroll depth as percentage
    const scrollableHeight = documentHeight - windowHeight;
    this.scrollDepth = scrollableHeight > 0 ? (scrollTop / scrollableHeight) * 100 : 0;

    // Track scroll
    this.tracking.trackScroll(this.scrollDepth, scrollTop);

    // Check if reached bottom (99% to account for rounding)
    if (this.scrollDepth >= 99 && !this.hasScrolledToBottom) {
      this.hasScrolledToBottom = true;
      console.log('User has scrolled to bottom - button enabled');
    }
  }

  /**
   * Check if button should be enabled
   */
  canProceed(): boolean {
    return this.hasScrolledToBottom;
  }

  /**
   * Finish reading and save metrics
   */
  finishReading(): void {
    if (!this.canProceed()) {
      alert('Please scroll to the bottom of the document to continue.');
      return;
    }

    this.tracking.saveMetrics().subscribe({
      next: () => {
        console.log('Condition 2 (Scroll Required) metrics saved');
        this.router.navigate(['/distractor-pattern-match']);
      },
      error: (err: any) => {
        console.error('Error saving metrics:', err);
        alert('Error saving data. Please contact the researcher.');
      }
    });
  }
}