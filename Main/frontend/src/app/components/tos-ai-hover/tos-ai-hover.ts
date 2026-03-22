// src/app/components/tos-ai-hover/tos-ai-hover.ts
import { Component, OnInit, OnDestroy, ViewChild, ElementRef, HostListener } from '@angular/core';
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
    private sanitizer: DomSanitizer
  ) {}

  ngOnInit(): void {
    window.scrollTo(0, 0);
    this.userId = sessionStorage.getItem('userName') || 'anonymous';
    this.loadTosDocument();
    this.initializeTracking();
  }

  ngOnDestroy(): void {
    this.tracking.endSession();
  }

  /**
   * Load the ToS document
   */
  loadTosDocument(): void {
    this.tosTitle = 'Service Terms of Service';
    this.tosId = 'ai-hover-tos-006';
    
    this.tosText = `Terms of Service

Last updated: January 2025

1. Acceptance of Terms
By accessing or using this Service, you agree to be bound by these Terms of Service. If you do not agree to the Terms, you may not access or use the Service.

2. Eligibility
You must be at least 16 years old to use the Service. By using the Service, you represent that you meet this age requirement.

3. User Accounts
To access certain features, you may be required to create an account. You are responsible for maintaining the confidentiality of your login credentials and for all activities that occur under your account.

4. Use of the Service
You agree not to use the Service for any unlawful purpose or to engage in any activity that may harm, disable, or impair the Service. You may not attempt to gain unauthorized access to any part of the Service.

5. Content Ownership
All content provided through the Service, including text, graphics, logos, and software, is the property of the Company or its licensors. You may not reproduce, distribute, or create derivative works from the content without explicit permission.

6. User-Generated Content
You may submit content such as comments or uploads. By submitting content, you grant the Company a non-exclusive, worldwide, royalty-free license to use, modify, reproduce, and distribute your content. You are responsible for ensuring your content does not violate the rights of others.

7. Privacy
Your use of the Service is also governed by our Privacy Policy, which describes how we collect, use, and share your information. By using the Service, you consent to the processing of your information in accordance with the Privacy Policy.

8. Payment and Subscriptions
Certain features may require payment. By subscribing, you authorize the Company to charge your payment method automatically on a recurring basis until you cancel. Prices may change, but we will notify you in advance of any changes.

9. Termination
We reserve the right to suspend or terminate your access to the Service at any time, with or without notice, if you violate these Terms or engage in harmful behaviour. Upon termination, your right to use the Service will immediately cease.

10. Disclaimer of Warranties
The Service is provided "as is" and "as available." We do not guarantee that the Service will be uninterrupted, error-free, or secure. Your use of the Service is at your own risk.

11. Limitation of Liability
The Company is not liable for any indirect, incidental, or consequential damages arising from your use of the Service. Our total liability to you will not exceed the amount you paid (if any) for using the Service in the past 12 months.

12. Modifications to the Terms
We may update these Terms from time to time. We will notify you of any material changes by posting the updated Terms on the Service. Continued use of the Service indicates acceptance of the revised Terms.

13. Governing Law
These Terms are governed by the laws of the United Kingdom. Any disputes will be resolved in the courts of England and Wales.

If you have any questions about these Terms, please contact us at support@example.com.`;

    this.highlightedHtml = this.sanitizer.bypassSecurityTrustHtml(
      this.escapeHtml(this.tosText)
    );
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
    this.currentClauseId = newId;

    if (!target) {
      this.tooltip = null;
      return;
    }

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
        alert('Study complete! Thank you for participating.');
        // TODO: Navigate to thank you page
        // this.router.navigate(['/thank-you']);
      },
      error: (err: any) => {
        console.error('Error saving metrics:', err);
        alert('Error saving data. Please contact the researcher.');
      }
    });
  }
}