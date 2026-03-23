// src/app/components/tos-ai-hover/tos-ai-hover.ts
import { Component, OnInit, OnDestroy, ViewChild, ElementRef, HostListener, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { TrackingService } from '../../services/tracking';
import { NlpApiService, NLPAnalysisResponse } from '../../services/nlp-api';

interface TooltipData {
  category: string;
  title: string;
  explanation: string;
  severity: 'high' | 'medium' | 'low';
  x: number;
  y: number;
}

@Component({
  selector: 'app-tos-ai-hover',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './tos-ai-hover.html',
  styleUrls: ['./tos-ai-hover.scss']
})
export class TosAiHoverComponent implements OnInit, OnDestroy {
  @ViewChild('tosContainer', { static: false }) tosContainer!: ElementRef;

  // ToS content
  tosText: string = '';
  tosTitle: string = '';
  tosId: string = 'ai-hover-tos-006';
  highlightedHtml: SafeHtml = '';

  // NLP Analysis
  analysis: NLPAnalysisResponse | null = null;
  isLoading: boolean = false;
  error: string | null = null;
  summaryGenerated: boolean = false;

  // Tooltip
  tooltip: TooltipData | null = null;
  private currentClauseId: string | null = null;

  // Tracking
  userId: string = '';
  scrollDepth: number = 0;

  constructor(
    private tracking: TrackingService,
    private nlpApi: NlpApiService,
    private router: Router,
    private sanitizer: DomSanitizer,
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
    this.tosTitle = 'SonicWave Terms of Service';
    this.tosId = 'ai-hover-tos-006';

    this.nlpApi.loadTosFile('musicstreaming_tos').subscribe({
      next: (text: string) => {
        this.tosText = text;
        this.highlightedHtml = this.sanitizer.bypassSecurityTrustHtml(
          this.escapeHtml(this.tosText)
        );
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
      'ai-hover' // Condition type
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
    
    const scrollableHeight = documentHeight - windowHeight;
    this.scrollDepth = scrollableHeight > 0 ? (scrollTop / scrollableHeight) * 100 : 0;

    this.tracking.trackScroll(this.scrollDepth, scrollTop);
  }

  /**
   * Generate AI summary
   */
  generateSummary(): void {
    this.isLoading = true;
    this.error = null;
    this.tooltip = null;
    this.currentClauseId = null;

    this.nlpApi.analyzeTos(this.tosText, 6, false).subscribe({
      next: (response: any) => {
        this.analysis = response;
        this.summaryGenerated = true;
        this.isLoading = false;

        // Apply subtle highlighting with hover
        this.applyHoverHighlighting();

        // Scroll to top so user sees the highlighted document
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

  /**
   * Apply subtle highlighting with hover capability
   */
  applyHoverHighlighting(): void {
    if (!this.analysis) return;

    interface Segment {
      start: number;
      end: number;
      category: string;
      severity: 'high' | 'medium' | 'low';
      title: string;
      explanation: string;
    }

    const segments: Segment[] = [];

    // Use the positions returned by the NLP API (they come from the same tosText we sent)
    Object.entries(this.analysis.grouped_clauses).forEach(([, group]: [string, any]) => {
      Object.entries(group.categories).forEach(([categoryName, category]: [string, any]) => {
        category.detections.forEach((detection: any) => {
          const start: number = detection.context?.position?.start ?? -1;
          const end: number   = detection.context?.position?.end   ?? -1;
          // Skip if positions are invalid or out of bounds
          if (start < 0 || end <= start || end > this.tosText.length) return;

          segments.push({
            start,
            end,
            category: categoryName,
            severity: group.severity as 'high' | 'medium' | 'low',
            title: category.metadata.title,
            explanation: category.metadata.explanation
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

    // Sort left-to-right for a single-pass HTML build
    noOverlap.sort((a, b) => a.start - b.start);

    // Build HTML in one pass — no position-shifting issues
    let html = '';
    let pos = 0;
    let clauseIndex = 0;

    for (const seg of noOverlap) {
      // Plain text before this segment
      html += this.escapeHtml(this.tosText.substring(pos, seg.start));
      // Highlighted span
      const cssClass = `clause-${seg.severity}`;
      const id = `clause-${clauseIndex++}`;
      const content = this.escapeHtml(this.tosText.substring(seg.start, seg.end));
      html += `<span class="${cssClass}" data-clause-id="${id}" data-category="${seg.category}" data-title="${this.escapeAttribute(seg.title)}" data-explanation="${this.escapeAttribute(seg.explanation)}" data-severity="${seg.severity}">${content}</span>`;
      pos = seg.end;
    }
    // Remaining plain text
    html += this.escapeHtml(this.tosText.substring(pos));

    this.highlightedHtml = this.sanitizer.bypassSecurityTrustHtml(html);
  }

  /**
   * Detect clause hover via document-level mousemove.
   * document:* HostListeners always run inside Angular's zone,
   * so change detection fires automatically.
   */
  @HostListener('document:mousemove', ['$event'])
  onDocumentMouseMove(event: MouseEvent): void {
    const target = (event.target as HTMLElement).closest('[data-clause-id]') as HTMLElement | null;
    const newId = target ? target.getAttribute('data-clause-id') : null;

    if (newId === this.currentClauseId) return;

    // Track hover leave on previous clause
    if (this.currentClauseId) {
      this.tracking.trackHoverLeave();
    }

    this.currentClauseId = newId;

    if (!target) {
      this.tooltip = null;
      return;
    }

    // Track hover enter on new clause
    const category = target.getAttribute('data-category') || '';
    this.tracking.trackHoverEnter(category, newId || '');

    const rect = target.getBoundingClientRect();
    this.tooltip = {
      category: target.getAttribute('data-category') || '',
      title: target.getAttribute('data-title') || '',
      explanation: target.getAttribute('data-explanation') || '',
      severity: target.getAttribute('data-severity') as 'high' | 'medium' | 'low',
      x: Math.min(rect.left, window.innerWidth - 340),
      y: Math.min(rect.bottom + 10, window.innerHeight - 160)
    };
  }

  /**
   * Escape HTML
   */
  private escapeHtml(text: string): string {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML.replace(/\n/g, '<br>');
  }

  /**
   * Escape HTML attributes
   */
  private escapeAttribute(text: string): string {
    return text.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  /**
   * Get severity color
   */
  getSeverityColor(severity: string): string {
    switch (severity) {
      case 'high': return 'red';
      case 'medium': return 'orange';
      case 'low': return 'green';
      default: return 'gray';
    }
  }

  /**
   * Get risk level
   */
  getRiskLevel(score: number): string {
    if (score >= 60) return 'high';
    if (score >= 30) return 'medium';
    return 'low';
  }

  /**
   * Get risk description
   */
  getRiskDescription(score: number): string {
    if (score >= 60) {
      return 'This Terms of Service contains several high-risk clauses that require careful attention.';
    } else if (score >= 30) {
      return 'This Terms of Service has moderate risk. Review the sections carefully.';
    } else {
      return 'This Terms of Service has relatively low risk compared to typical agreements.';
    }
  }

  /**
   * Finish reading and save metrics
   */
  finishReading(): void {
    this.tracking.saveMetrics().subscribe({
      next: () => {
        console.log('Condition 6 (AI Hover) metrics saved');
        // Navigate to thank you page
        this.router.navigate(['/thank-you']);
      },
      error: (err: any) => {
        console.error('Error saving metrics:', err);
        alert('Error saving data. Please contact the researcher.');
      }
    });
  }
}