// src/app/components/tos-ai-enhanced/tos-ai-enhanced.ts
import { Component, OnInit, OnDestroy, ViewChild, ElementRef, HostListener, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { Router } from '@angular/router';
import { NlpApiService, NLPAnalysisResponse, ClauseDetection } from '../../services/nlp-api';
import { TrackingService } from '../../services/tracking';
import { EyeTrackingService } from '../../services/eye-tracking';

@Component({
  selector: 'app-tos-ai-enhanced',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './tos-ai-enhanced.html',
  styleUrls: ['./tos-ai-enhanced.scss']
})
export class TosAiEnhancedComponent implements OnInit, OnDestroy {
  @ViewChild('tosContainer', { static: false }) tosContainer!: ElementRef;

  // ToS content
  tosText: string = '';
  tosTitle: string = '';
  tosId: string = 'sample-tos-001';
  highlightedHtml: SafeHtml = '';

  // NLP Analysis
  analysis: NLPAnalysisResponse | null = null;
  isLoading: boolean = false;
  error: string | null = null;

  // UI State
  summaryGenerated: boolean = false;
  showSummary: boolean = false;

  // Tracking
  userId: string = '';
  scrollDepth: number = 0;

  constructor(
    private nlpApi: NlpApiService,
    private tracking: TrackingService,
    private router: Router,
    private cdr: ChangeDetectorRef,
    private sanitizer: DomSanitizer,
    private eyeTracking: EyeTrackingService
  ) {}

  ngOnInit(): void {
    window.scrollTo(0, 0);
    this.userId = sessionStorage.getItem('userName') || 'anonymous';
    this.loadTosDocument();
  }

  ngOnDestroy(): void {
    this.eyeTracking.stopTracking(this.tracking.getSessionId());
    this.tracking.endSession();
  }

  // Load the ToS document from the server
  loadTosDocument(): void {
    this.tosTitle = 'PulseFit Terms of Service';
    this.tosId = 'ai-enhanced-tos-005';

    this.nlpApi.loadTosFile('fitness_tos').subscribe({
      next: (text: string) => {
        this.tosText = text;
        this.highlightedHtml = this.escapeHtml(this.tosText);
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
      'ai-enhanced'
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

  // Generate summary using NLP API
  generateSummary(): void {
    this.isLoading = true;
    this.error = null;

    this.nlpApi.analyzeTos(this.tosText, 6, false).subscribe({
      next: (response: any) => {
        this.analysis = response;
        this.summaryGenerated = true;
        this.showSummary = true;
        this.isLoading = false;

        // Apply highlighting to the ToS text
        this.applyHighlighting();

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

  // Apply syntax highlighting to detected clauses in the ToS
  applyHighlighting(): void {
    if (!this.analysis) return;

    interface Segment {
      start: number;
      end: number;
      category: string;
      severity: 'high' | 'medium' | 'low';
    }

    const segments: Segment[] = [];

    // Collect all detections with their positions
    Object.entries(this.analysis.grouped_clauses).forEach(([, group]: [string, any]) => {
      Object.entries(group.categories).forEach(([categoryName, category]: [string, any]) => {
        category.detections.forEach((detection: any) => {
          const start: number = detection.context?.position?.start ?? -1;
          const end: number = detection.context?.position?.end ?? -1;
          if (start < 0 || end <= start || end > this.tosText.length) return;

          segments.push({
            start,
            end,
            category: categoryName,
            severity: group.severity as 'high' | 'medium' | 'low'
          });
        });
      });
    });

    // Sort rightmost-first, then remove overlapping segments
    segments.sort((a, b) => b.start - a.start);
    const noOverlap: Segment[] = [];
    let boundary = Infinity;
    for (const seg of segments) {
      if (seg.end <= boundary) {
        noOverlap.push(seg);
        boundary = seg.start;
      }
    }

    // Sort left-to-right for single-pass HTML build
    noOverlap.sort((a, b) => a.start - b.start);

    // Build HTML in one pass
    let html = '';
    let pos = 0;

    for (const seg of noOverlap) {
      html += this.escapeHtml(this.tosText.substring(pos, seg.start));
      const cssClass = `highlight-${seg.severity}`;
      const content = this.escapeHtml(this.tosText.substring(seg.start, seg.end));
      html += `<span class="${cssClass}" data-category="${this.escapeAttribute(seg.category)}" data-start="${seg.start}" data-end="${seg.end}" style="cursor:pointer">${content}</span>`;
      pos = seg.end;
    }
    html += this.escapeHtml(this.tosText.substring(pos));

    this.highlightedHtml = this.sanitizer.bypassSecurityTrustHtml(html);
  }

  // Handle clicks on highlighted clauses via event delegation
  @HostListener('click', ['$event'])
  onHostClick(event: MouseEvent): void {
    const target = (event.target as HTMLElement).closest('[data-category]') as HTMLElement | null;
    if (!target) return;

    const category = target.getAttribute('data-category') || '';
    const start = parseInt(target.getAttribute('data-start') || '0', 10);
    const end = parseInt(target.getAttribute('data-end') || '0', 10);
    this.onClauseClick(category, start, end);
  }

  // Escape an attribute value
  private escapeAttribute(value: string): string {
    return value.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  // Handle click on highlighted clause
  onClauseClick(category: string, start: number, end: number): void {
    // Track the click
    this.tracking.trackClauseClick(category, { start, end });

    // Show explanation modal or tooltip
    console.log('Clause clicked:', category);
    const categoryData = this.findCategoryData(category);

    if (categoryData) {
      alert(`${categoryData.metadata.title}\n\n${categoryData.metadata.explanation}`);
    }
  }

  // Find category data for explanation
  private findCategoryData(category: string): any {
    if (!this.analysis) return null;

    for (const group of Object.values(this.analysis.grouped_clauses)) {
      const typedGroup = group as any;
      if (typedGroup.categories[category]) {
        return typedGroup.categories[category];
      }
    }
    return null;
  }

  // Escape HTML to prevent XSS
  private escapeHtml(text: string): string {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML.replace(/\n/g, '<br>\n');
  }

  // Get severity badge color
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

  // Show context for a detection (scroll to position in document)
  showContext(detection: ClauseDetection): void {
    const position = detection.context.position.start;
    
    // Scroll to the position in the document
    window.scrollTo({
      top: position,
      behavior: 'smooth'
    });
  }

  // Save metrics and proceed
  proceedToNextPhase(): void {
    this.tracking.saveMetrics().subscribe({
      next: () => {
        console.log('Metrics saved successfully');
        // Navigate to condition 6
        this.router.navigate(['/distractor-spot-difference']);
      },
      error: (err: any) => {
        console.error('Error saving metrics:', err);
      }
    });
  }
}