// src/app/components/tos-viewer/tos-viewer.ts
import { Component, OnInit, OnDestroy, ViewChild, ElementRef, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NlpApiService, NLPAnalysisResponse, ClauseDetection } from '../../services/nlp-api';
import { TrackingService } from '../../services/tracking';

interface HighlightedSection {
  start: number;
  end: number;
  category: string;
  severity: 'high' | 'medium' | 'low';
  detection: ClauseDetection;
}

@Component({
  selector: 'app-tos-viewer',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './tos-viewer.html',
  styleUrls: ['./tos-viewer.scss']
})
export class TosViewerComponent implements OnInit, OnDestroy {
  @ViewChild('tosContainer', { static: false }) tosContainer!: ElementRef;

  // ToS content
  tosText: string = '';
  tosTitle: string = '';
  tosId: string = 'sample-tos-001';
  highlightedHtml: string = '';

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
    private tracking: TrackingService
  ) {
    // Get user name from session storage
    this.userId = sessionStorage.getItem('userName') || 'anonymous';
  }

  ngOnInit(): void {
    this.loadTosDocument();
    this.initializeTracking();
  }

  ngOnDestroy(): void {
    this.tracking.endSession();
  }

  /**
   * Load the ToS document (in real app, this would come from backend)
   */
  loadTosDocument(): void {
    // For now, load from sample. In production, fetch from your backend
    // based on randomization or study condition
    this.tosTitle = 'Sample Service Terms of Service';
    this.tosId = 'sample-tos-001';
    
    // You would typically fetch this from your backend:
    // this.http.get<{text: string, title: string}>(`/api/tos/${this.tosId}`)
    
    // For now, using a sample
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

    this.highlightedHtml = this.escapeHtml(this.tosText);
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
      'treatment'
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
   * Generate summary using NLP API
   */
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
   * Apply syntax highlighting to detected clauses in the ToS
   */
  applyHighlighting(): void {
    if (!this.analysis) return;

    const highlights: HighlightedSection[] = [];

    // Collect all detections with their positions
    Object.entries(this.analysis.grouped_clauses).forEach(([groupName, group]: [string, any]) => {
      Object.entries(group.categories).forEach(([categoryName, category]: [string, any]) => {
        category.detections.forEach((detection: any) => {
          highlights.push({
            start: detection.context.position.start,
            end: detection.context.position.end,
            category: categoryName,
            severity: group.severity,
            detection
          });
        });
      });
    });

    // Sort by position (start) in reverse to avoid position shifts when inserting HTML
    highlights.sort((a, b) => b.start - a.start);

    // Apply highlighting
    let highlightedText = this.tosText;
    
    highlights.forEach((highlight) => {
      const before = highlightedText.substring(0, highlight.start);
      const text = highlightedText.substring(highlight.start, highlight.end);
      const after = highlightedText.substring(highlight.end);

      const cssClass = `highlight-${highlight.severity}`;
      const dataAttr = `data-category="${highlight.category}"`;
      
      highlightedText = 
        before +
        `<span class="${cssClass}" ${dataAttr} (click)="onClauseClick('${highlight.category}', ${highlight.start}, ${highlight.end})">${text}</span>` +
        after;
    });

    this.highlightedHtml = highlightedText.replace(/\n/g, '<br>');
  }

  /**
   * Handle click on highlighted clause
   */
  onClauseClick(category: string, start: number, end: number): void {
    // Track the click
    this.tracking.trackClauseClick(category, { start, end });

    // Show explanation modal or tooltip
    // For now, just log
    console.log('Clause clicked:', category);
    
    // You could show a modal with the explanation here
    const categoryData = this.findCategoryData(category);
    if (categoryData) {
      alert(`${categoryData.metadata.title}\n\n${categoryData.metadata.explanation}`);
    }
  }

  /**
   * Find category data for explanation
   */
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

  /**
   * Escape HTML to prevent XSS
   */
  private escapeHtml(text: string): string {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML.replace(/\n/g, '<br>');
  }

  /**
   * Get severity badge color
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
   * Get risk level category
   */
  getRiskLevel(score: number): string {
    if (score >= 60) return 'high';
    if (score >= 30) return 'medium';
    return 'low';
  }

  /**
   * Get risk description based on score
   */
  getRiskDescription(score: number): string {
    if (score >= 60) {
      return 'This Terms of Service contains several high-risk clauses that require careful attention.';
    } else if (score >= 30) {
      return 'This Terms of Service has moderate risk. Review the highlighted sections carefully.';
    } else {
      return 'This Terms of Service has relatively low risk compared to typical agreements.';
    }
  }

  /**
   * Show context for a detection (scroll to position in document)
   */
  showContext(detection: ClauseDetection): void {
    const position = detection.context.position.start;
    
    // Scroll to the position in the document
    window.scrollTo({
      top: position,
      behavior: 'smooth'
    });

    // Optionally highlight temporarily
    // You could add a temporary highlight class here
  }

  /**
   * Save metrics and proceed (call this when user moves to next phase)
   */
  proceedToNextPhase(): void {
    this.tracking.saveMetrics().subscribe({
      next: () => {
        console.log('Metrics saved successfully');
        // Navigate to next phase of your study
      },
      error: (err: any) => {
        console.error('Error saving metrics:', err);
      }
    });
  }
}