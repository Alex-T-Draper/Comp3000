// src/app/components/tos-ai-summary/tos-ai-summary.ts
import { Component, OnInit, OnDestroy, ViewChild, ElementRef, HostListener, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { TrackingService } from '../../services/tracking';
import { NlpApiService, NLPAnalysisResponse } from '../../services/nlp-api';
import { EyeTrackingService } from '../../services/eye-tracking';

@Component({
  selector: 'app-tos-ai-summary',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './tos-ai-summary.html',
  styleUrls: ['./tos-ai-summary.scss']
})
export class TosAiSummaryComponent implements OnInit, OnDestroy {
  @ViewChild('tosContainer', { static: false }) tosContainer!: ElementRef;

  // ToS content
  tosText: string = '';
  tosTitle: string = '';
  tosId: string = 'ai-summary-tos-004';

  // NLP Analysis
  analysis: NLPAnalysisResponse | null = null;
  isLoading: boolean = false;
  error: string | null = null;
  summaryGenerated: boolean = false;

  // Tracking
  userId: string = '';
  scrollDepth: number = 0;

  constructor(
    private tracking: TrackingService,
    private nlpApi: NlpApiService,
    private router: Router,
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

  // Load the ToS document
  loadTosDocument(): void {
    this.tosTitle = 'LearnVault Terms of Service';
    this.tosId = 'ai-summary-tos-004';

    this.nlpApi.loadTosFile('education_tos').subscribe({
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

  // Initialize tracking session
  initializeTracking(): void {
    this.tracking.startSession(
      this.userId,
      this.tosId,
      this.tosText,
      this.tosTitle,
      'ai-summary' // Condition type
    );
    this.eyeTracking.startTracking(this.tracking.getSessionId());
  }

  // Handle scroll events for tracking
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

  // Generate AI summary
  generateSummary(): void {
    this.isLoading = true;
    this.error = null;

    this.nlpApi.analyzeTos(this.tosText, 6, false).subscribe({
      next: (response: any) => {
        this.analysis = response;
        this.summaryGenerated = true;
        this.isLoading = false;

        // Scroll to top so user sees the summary panel
        window.scrollTo({ top: 0, behavior: 'smooth' });

        // Track summary generation
        const categories = Object.keys(response.grouped_clauses);
        this.tracking.trackSummaryGeneration(
          response.risk.normalized_percent,
          categories
        );
      },
      error: (err: any) => {
        console.error('Error generating summary:', err);
        this.error = 'Failed to generate summary. Please try again.';
        this.isLoading = false;
      }
    });
  }

  // Get severity color
  getSeverityColor(severity: string): string {
    switch (severity) {
      case 'high': return 'red';
      case 'medium': return 'orange';
      case 'low': return 'green';
      default: return 'gray';
    }
  }

  // Get risk level category
  getRiskLevel(score: number): string {
    if (score >= 60) return 'high';
    if (score >= 30) return 'medium';
    return 'low';
  }

  // Get risk description based on score
  getRiskDescription(score: number): string {
    if (score >= 60) {
      return 'This Terms of Service contains several high-risk clauses that require careful attention.';
    } else if (score >= 30) {
      return 'This Terms of Service has moderate risk. Review the highlighted sections carefully.';
    } else {
      return 'This Terms of Service has relatively low risk compared to typical agreements.';
    }
  }

  // Finish reading and save metrics
  finishReading(): void {
    this.tracking.saveMetrics().subscribe({
      next: () => {
        console.log('Condition 4 (AI Summary) metrics saved');
        // Navigate to Condition 5
        this.router.navigate(['/distractor-reaction-time']);
      },
      error: (err: any) => {
        console.error('Error saving metrics:', err);
        alert('Error saving data. Please contact the researcher.');
      }
    });
  }
}