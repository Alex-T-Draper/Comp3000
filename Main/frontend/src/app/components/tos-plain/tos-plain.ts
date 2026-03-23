// src/app/components/tos-plain/tos-plain.ts
import { Component, OnInit, OnDestroy, ViewChild, ElementRef, HostListener, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { TrackingService } from '../../services/tracking';
import { NlpApiService } from '../../services/nlp-api';

@Component({
  selector: 'app-tos-plain',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './tos-plain.html',
  styleUrls: ['./tos-plain.scss']
})
export class TosPlainComponent implements OnInit, OnDestroy {
  @ViewChild('tosContainer', { static: false }) tosContainer!: ElementRef;

  // ToS content
  tosText: string = '';
  tosTitle: string = '';
  tosId: string = 'plain-tos-001';

  // Tracking
  userId: string = '';
  scrollDepth: number = 0;

  constructor(
    private tracking: TrackingService,
    private router: Router,
    private nlpApi: NlpApiService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    window.scrollTo(0, 0);
    this.userId = sessionStorage.getItem('userName') || 'anonymous';
    this.loadTosDocument();
  }

  ngOnDestroy(): void {
    this.tracking.endSession();
  }

  /**
   * Load the ToS document
   */
  loadTosDocument(): void {
    this.tosTitle = 'BazaarBox Terms of Service';
    this.tosId = 'plain-tos-001';

    this.nlpApi.loadTosFile('ecommerce_tos').subscribe({
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
      'control' // Condition type
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
  }

  /**
   * Finish reading and save metrics
   */
  finishReading(): void {
    this.tracking.saveMetrics().subscribe({
      next: () => {
        console.log('Condition 1 (Plain) metrics saved');
        this.router.navigate(['/tos-scroll-required']);
      },
      error: (err: any) => {
        console.error('Error saving metrics:', err);
        alert('Error saving data. Please contact the researcher.');
      }
    });
  }
}