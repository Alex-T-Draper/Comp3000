// src/app/components/tos-formatted/tos-formatted.ts
import { Component, OnInit, OnDestroy, ViewChild, ElementRef, HostListener, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { Router } from '@angular/router';
import { TrackingService } from '../../services/tracking';
import { NlpApiService } from '../../services/nlp-api';
import { EyeTrackingService } from '../../services/eye-tracking';

@Component({
  selector: 'app-tos-formatted',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './tos-formatted.html',
  styleUrls: ['./tos-formatted.scss']
})
export class TosFormattedComponent implements OnInit, OnDestroy {
  @ViewChild('tosContainer', { static: false }) tosContainer!: ElementRef;

  // ToS content
  tosText: string = '';
  tosTitle: string = '';
  tosId: string = 'formatted-tos-003';
  formattedHtml: SafeHtml = '';

  // Tracking
  userId: string = '';
  scrollDepth: number = 0;

  constructor(
    private tracking: TrackingService,
    private router: Router,
    private sanitizer: DomSanitizer,
    private nlpApi: NlpApiService,
    private cdr: ChangeDetectorRef,
    private eyeTracking: EyeTrackingService
  ) {}

  ngOnInit(): void {
    window.scrollTo(0, 0);
    // Get user name from session storage
    this.userId = sessionStorage.getItem('userName') || 'anonymous';
    this.loadTosDocument();
  }

  ngOnDestroy(): void {
    this.eyeTracking.stopTracking(this.tracking.getSessionId());
    this.tracking.endSession();
  }

  /**
   * Load the ToS document
   */
  loadTosDocument(): void {
    this.tosTitle = 'ConnectSphere Terms of Service';
    this.tosId = 'formatted-tos-003';

    this.nlpApi.loadTosFile('socialmedia_tos').subscribe({
      next: (text: string) => {
        this.tosText = text;
        this.applyFormatting();
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
   * Apply keyword-based formatting to the ToS text
   */
  applyFormatting(): void {
    // First escape HTML to prevent injection
    let formatted = this.escapeHtml(this.tosText);

    // High-risk keywords (red highlight) — clauses with significant legal impact
    const highRiskKeywords = [
      // Data sharing & privacy
      'may share your information',
      'share your data',
      'share your personal',
      'third-party advertising',
      'targeted advertising',
      'third parties',
      'disclose your information',
      'sell your data',
      'sell your information',
      'tracking technologies',
      'retain your personal data',
      'retain your data',
      'copies may persist',
      // Liability & warranties
      'not be liable',
      'not liable',
      'no liability',
      'as is',
      'as available',
      'without warranties',
      'disclaimer of warranties',
      'disclaims all warranties',
      'limitation of liability',
      'punitive damages',
      'consequential damages',
      'loss of profits',
      'loss of data',
      // Dispute & arbitration
      'binding arbitration',
      'arbitration',
      'waive your right',
      'class action',
      'class-wide arbitration',
      // Account & termination
      'terminate your account',
      'terminate your access',
      'suspend or terminate',
      'without cause',
      'without notice',
      'without prior notice',
      'account deletion is permanent',
      // Indemnification
      'indemnify',
      'hold harmless',
      // Content rights
      'sublicensable',
      'transferable license',
      'continues even after',
      'irrevocable',
      'perpetual license',
      // Changes & assignment
      'modify these terms at any time',
      'assign or transfer',
      'without your prior consent',
    ];

    // Medium-risk keywords (yellow highlight) — important but less severe
    const mediumRiskKeywords = [
      // Payments & subscriptions
      'payment',
      'subscription',
      'automatically',
      'auto-renew',
      'charge your payment',
      'recurring basis',
      'until you cancel',
      'prices may change',
      'non-refundable',
      'no refund',
      // Content licensing
      'grant connectsphere',
      'grant the company',
      'grant us',
      'grant pulsefit',
      'license to use',
      'royalty-free',
      'worldwide',
      'derivative works',
      'create derivative',
      // Data collection
      'cookies',
      'web beacons',
      'pixels',
      'usage data',
      'device identifiers',
      'ip address',
      'click patterns',
      'interaction data',
      'personalise your experience',
      'personalize your experience',
      // Account & moderation
      'sole discretion',
      'at our discretion',
      'reserve the right',
      'prolonged inactivity',
      'we may remove',
      'content moderation',
      // Law & jurisdiction
      'governing law',
      'jurisdiction',
      'applicable law',
    ];

    // Important phrases to bold — user obligations & acknowledgements
    const boldKeywords = [
      'you agree',
      'you must',
      'you are required',
      'you are responsible',
      'you are solely responsible',
      'you consent',
      'you acknowledge',
      'you acknowledge and consent',
      'you authorize',
      'you represent',
      'you warrant',
      'you may not',
      'you agree not to',
      'you agree to indemnify',
      'you waive',
      'your responsibility',
      'you retain ownership',
    ];

    // Sort each list by length descending so longer phrases match first
    highRiskKeywords.sort((a, b) => b.length - a.length);
    mediumRiskKeywords.sort((a, b) => b.length - a.length);
    boldKeywords.sort((a, b) => b.length - a.length);

    // Apply high-risk highlighting (case insensitive)
    highRiskKeywords.forEach(keyword => {
      const regex = new RegExp(`(${this.escapeRegex(keyword)})`, 'gi');
      formatted = formatted.replace(regex, '<span class="highlight-high">$1</span>');
    });

    // Apply medium-risk highlighting
    mediumRiskKeywords.forEach(keyword => {
      const regex = new RegExp(`(${this.escapeRegex(keyword)})`, 'gi');
      formatted = formatted.replace(regex, '<span class="highlight-medium">$1</span>');
    });

    // Apply bold to important phrases
    boldKeywords.forEach(keyword => {
      const regex = new RegExp(`(${this.escapeRegex(keyword)})`, 'gi');
      formatted = formatted.replace(regex, '<strong class="bold-important">$1</strong>');
    });

    // Preserve line breaks
    formatted = formatted.replace(/\n/g, '<br>');

    // Sanitize and mark as safe HTML
    this.formattedHtml = this.sanitizer.bypassSecurityTrustHtml(formatted);
  }

  /**
   * Escape HTML characters to prevent XSS
   */
  private escapeHtml(text: string): string {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  /**
   * Escape special regex characters
   */
  private escapeRegex(str: string): string {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
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
      'formatted' // Condition type
    );
    this.eyeTracking.startTracking(this.tracking.getSessionId());
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

    // Update eye tracking with scroll position
    this.eyeTracking.updateScrollPosition(scrollTop);
  }

  /**
   * Finish reading and save metrics
   */
  finishReading(): void {
    this.tracking.saveMetrics().subscribe({
      next: () => {
        console.log('Condition 3 (Formatted) metrics saved');
        // Navigate to Condition 4
        this.router.navigate(['/distractor-math-quiz']);
      },
      error: (err: any) => {
        console.error('Error saving metrics:', err);
        alert('Error saving data. Please contact the researcher.');
      }
    });
  }
}