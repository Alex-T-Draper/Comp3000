// src/app/services/tracking.ts - Updated for database backend
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface ScrollEvent {
  timestamp: Date;
  scrollDepth: number; // 0-100 percentage
  scrollPosition: number; // pixels from top
}

export interface UserMetrics {
  // Session info
  sessionId: string;
  userId: string;  // User's name
  tosId: string;
  conditionGroup: 'control' | 'scroll-gate' | 'formatted' | 'ai-summary' | 'ai-enhanced';
  
  // Document info
  tosLength: number; // word count
  tosTitle: string;
  
  // Reading behavior
  timeStarted: Date;
  timeEnded?: Date;
  totalReadingTime?: number; // seconds
  timeToBottom?: number; // seconds until scrolled to 100%
  timeBeforeSummary?: number; // seconds before clicking "Generate Summary"
  didReadComplete: boolean; // reached 100% scroll
  
  // Scroll tracking
  scrollEvents: ScrollEvent[];
  maxScrollDepth: number; // highest % they reached
  scrollBehavior: 'quick-scroll' | 'thorough-read' | 'partial-read';
  
  // Engagement with summary
  summaryGenerated: boolean;
  summaryGeneratedAt?: Date;
  clausesClicked: Array<{
    category: string;
    timestamp: Date;
    position: { start: number; end: number };
  }>;
  
  // NLP Results (for later analysis correlation)
  riskScore?: number;
  detectedCategories?: string[];
}

@Injectable({
  providedIn: 'root'
})
export class TrackingService {
  private metrics: UserMetrics;
  private scrollTrackingInterval: any;
  private apiUrl = 'http://127.0.0.1:8000/api'; // Your FastAPI backend

  constructor(private http: HttpClient) {
    this.metrics = this.initializeMetrics();
  }

  /**
   * Initialize a new tracking session
   */
  startSession(userName: string, tosId: string, tosText: string, tosTitle: string, conditionGroup: 'control' | 'scroll-gate' | 'formatted' | 'ai-summary' | 'ai-enhanced' = 'control'): void {
    this.metrics = {
      sessionId: this.generateSessionId(),
      userId: userName,  // Use the user's name
      tosId,
      tosTitle,
      conditionGroup,
      tosLength: this.countWords(tosText),
      timeStarted: new Date(),
      didReadComplete: false,
      scrollEvents: [],
      maxScrollDepth: 0,
      scrollBehavior: 'partial-read',
      summaryGenerated: false,
      clausesClicked: []
    };
  }

  /**
   * Track scroll position
   */
  trackScroll(scrollDepth: number, scrollPosition: number): void {
    const event: ScrollEvent = {
      timestamp: new Date(),
      scrollDepth,
      scrollPosition
    };

    this.metrics.scrollEvents.push(event);
    
    // Update max scroll depth
    if (scrollDepth > this.metrics.maxScrollDepth) {
      this.metrics.maxScrollDepth = scrollDepth;
    }

    // Check if reached bottom
    if (scrollDepth >= 99 && !this.metrics.didReadComplete) {
      this.metrics.didReadComplete = true;
      this.metrics.timeToBottom = this.getElapsedSeconds();
    }
  }

  /**
   * Track when user clicks "Generate Summary"
   */
  trackSummaryGeneration(riskScore: number, categories: string[]): void {
    this.metrics.summaryGenerated = true;
    this.metrics.summaryGeneratedAt = new Date();
    this.metrics.timeBeforeSummary = this.getElapsedSeconds();
    this.metrics.riskScore = riskScore;
    this.metrics.detectedCategories = categories;
  }

  /**
   * Track when user clicks on a highlighted clause
   */
  trackClauseClick(category: string, position: { start: number; end: number }): void {
    this.metrics.clausesClicked.push({
      category,
      timestamp: new Date(),
      position
    });
  }

  /**
   * End the session and calculate final metrics
   */
  endSession(): void {
    this.metrics.timeEnded = new Date();
    this.metrics.totalReadingTime = this.getElapsedSeconds();
    this.metrics.scrollBehavior = this.determineScrollBehavior();
    
    this.stopScrollTracking();
  }

  /**
   * Send metrics to backend for analysis
   */
  saveMetrics(): Observable<any> {
    this.endSession();
    
    // Convert dates to ISO strings for JSON serialization
    const metricsToSave = {
      ...this.metrics,
      timeStarted: this.metrics.timeStarted.toISOString(),
      timeEnded: this.metrics.timeEnded?.toISOString(),
      summaryGeneratedAt: this.metrics.summaryGeneratedAt?.toISOString(),
      scrollEvents: this.metrics.scrollEvents.map(e => ({
        ...e,
        timestamp: e.timestamp.toISOString()
      })),
      clausesClicked: this.metrics.clausesClicked.map(c => ({
        ...c,
        timestamp: c.timestamp.toISOString()
      }))
    };
    
    return this.http.post(`${this.apiUrl}/metrics`, metricsToSave);
  }

  /**
   * Get current metrics (for debugging or real-time display)
   */
  getCurrentMetrics(): UserMetrics {
    return { ...this.metrics };
  }

  // Private helper methods

  private initializeMetrics(): UserMetrics {
    return {
      sessionId: '',
      userId: '',
      tosId: '',
      tosTitle: '',
      conditionGroup: 'control',
      tosLength: 0,
      timeStarted: new Date(),
      didReadComplete: false,
      scrollEvents: [],
      maxScrollDepth: 0,
      scrollBehavior: 'partial-read',
      summaryGenerated: false,
      clausesClicked: []
    };
  }

  private generateSessionId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  private countWords(text: string): number {
    return text.trim().split(/\s+/).length;
  }

  private getElapsedSeconds(): number {
    const elapsed = new Date().getTime() - this.metrics.timeStarted.getTime();
    return Math.floor(elapsed / 1000);
  }

  private determineScrollBehavior(): 'quick-scroll' | 'thorough-read' | 'partial-read' {
    const readingTime = this.getElapsedSeconds();
    const wordsPerMinute = (this.metrics.tosLength / readingTime) * 60;
    
    // Average reading speed is 200-250 WPM
    // Quick scroll: > 500 WPM (clearly not reading)
    // Thorough read: 150-300 WPM (actually reading)
    // Partial read: everything else
    
    if (wordsPerMinute > 500) {
      return 'quick-scroll';
    } else if (wordsPerMinute >= 150 && wordsPerMinute <= 300 && this.metrics.didReadComplete) {
      return 'thorough-read';
    } else {
      return 'partial-read';
    }
  }

  private startScrollTracking(): void {
    // This will be called from the component with actual scroll values
    // The interval here is just a placeholder for periodic checks
  }

  private stopScrollTracking(): void {
    if (this.scrollTrackingInterval) {
      clearInterval(this.scrollTrackingInterval);
    }
  }
}