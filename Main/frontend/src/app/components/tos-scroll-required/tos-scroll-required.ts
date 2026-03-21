// src/app/components/tos-scroll-required/tos-scroll-required.ts
import { Component, OnInit, OnDestroy, ViewChild, ElementRef, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { TrackingService } from '../../services/tracking';

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
    private router: Router
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
   * Load the ToS document
   */
  loadTosDocument(): void {
    this.tosTitle = 'Service Terms of Service';
    this.tosId = 'scroll-required-tos-002';
    
    // Sample ToS text - in production, load from backend
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
        this.router.navigate(['/tos-formatted']);
      },
      error: (err: any) => {
        console.error('Error saving metrics:', err);
        alert('Error saving data. Please contact the researcher.');
      }
    });
  }
}