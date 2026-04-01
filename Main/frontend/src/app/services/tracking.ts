// src/app/services/tracking.ts - Updated for database backend
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface ScrollEvent {
  timestamp: Date;
  scrollDepth: number; // 0-100 percentage
  scrollPosition: number; // pixels from top
  direction: 'up' | 'down'; // scroll direction
}

export interface PauseEvent {
  timestamp: Date;
  scrollDepth: number; // where they paused
  duration: number; // seconds paused
}

export interface HoverEvent {
  category: string;
  clauseId: string;
  timestamp: Date;
  duration: number; // milliseconds spent hovering
}

export interface UserMetrics {
  // Session info
  sessionId: string;
  userId: string;  // User's name
  tosId: string;
  conditionGroup: 'control' | 'scroll-gate' | 'formatted' | 'ai-summary' | 'ai-enhanced' | 'ai-hover';
  
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
  
  // Re-read & direction tracking
  scrollUpCount: number; // number of times user scrolled back up
  reReadSections: number; // times user scrolled back >10% to re-read
  
  // Pause/dwell tracking
  pauseEvents: PauseEvent[]; // periods where user paused scrolling (reading)
  totalPauseTime: number; // total seconds paused (reading) vs scrolling
  
  // Summary engagement
  summaryGenerated: boolean;
  summaryGeneratedAt?: Date;
  summaryViewDuration?: number; // seconds spent viewing summary after generation
  
  // Clause interactions
  clausesClicked: Array<{
    category: string;
    timestamp: Date;
    position: { start: number; end: number };
  }>;
  
  // Hover tracking (for ai-hover condition)
  hoverEvents: HoverEvent[];
  
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
  private apiUrl = 'http://127.0.0.1:8000/api'; 

  // Pause detection state
  private lastScrollTime: number = 0;
  private lastScrollDepth: number = 0;
  private pauseTimer: any = null;
  private pauseStartTime: number = 0;
  private readonly PAUSE_THRESHOLD_MS = 3000; // 3 seconds = a reading pause

  // Scroll-up gesture tracking
  private lastDirection: 'up' | 'down' = 'down'; // track direction changes, not every event
  private peakScrollDepth: number = 0; // highest depth reached (for re-read detection)

  // Hover tracking state
  private currentHoverStart: number = 0;
  private currentHoverCategory: string = '';
  private currentHoverClauseId: string = '';

  constructor(private http: HttpClient) {
    this.metrics = this.initializeMetrics();
  }

  // Initialize a new tracking session
  startSession(userName: string, tosId: string, tosText: string, tosTitle: string, conditionGroup: 'control' | 'scroll-gate' | 'formatted' | 'ai-summary' | 'ai-enhanced' | 'ai-hover' = 'control'): void {
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
      scrollUpCount: 0,
      reReadSections: 0,
      pauseEvents: [],
      totalPauseTime: 0,
      summaryGenerated: false,
      clausesClicked: [],
      hoverEvents: []
    };

    this.lastScrollTime = Date.now();
    this.lastScrollDepth = 0;
    this.lastDirection = 'down';
    this.peakScrollDepth = 0;
  }

  // Track scroll position with direction and pause detection
  trackScroll(scrollDepth: number, scrollPosition: number): void {
    const now = Date.now();
    const direction: 'up' | 'down' = scrollDepth >= this.lastScrollDepth ? 'down' : 'up';

    const event: ScrollEvent = {
      timestamp: new Date(),
      scrollDepth,
      scrollPosition,
      direction
    };

    this.metrics.scrollEvents.push(event);
    
    // Track scroll-up gestures (only count direction *changes*, not every event)
    if (direction === 'up' && this.lastDirection === 'down') {
      this.metrics.scrollUpCount++;

      // Significant re-read: user is now >10% above their peak scroll depth
      if (this.peakScrollDepth - scrollDepth > 10) {
        this.metrics.reReadSections++;
      }
    }
    this.lastDirection = direction;

    // Update peak and max scroll depth
    if (scrollDepth > this.peakScrollDepth) {
      this.peakScrollDepth = scrollDepth;
    }
    if (scrollDepth > this.metrics.maxScrollDepth) {
      this.metrics.maxScrollDepth = scrollDepth;
    }

    // Check if reached bottom
    if (scrollDepth >= 99 && !this.metrics.didReadComplete) {
      this.metrics.didReadComplete = true;
      this.metrics.timeToBottom = this.getElapsedSeconds();
    }

    // Pause/dwell detection: if user stops scrolling for 3+ seconds, record it
    this.detectPause(scrollDepth, now);

    this.lastScrollDepth = scrollDepth;
    this.lastScrollTime = now;
  }

  // Detect reading pauses (user stops scrolling for PAUSE_THRESHOLD_MS)
  private detectPause(currentDepth: number, now: number): void {
    // Clear previous timer
    if (this.pauseTimer) {
      clearTimeout(this.pauseTimer);
    }

    // If there was an active pause, finalize it
    if (this.pauseStartTime > 0) {
      const duration = (now - this.pauseStartTime) / 1000;
      if (duration >= this.PAUSE_THRESHOLD_MS / 1000) {
        this.metrics.pauseEvents.push({
          timestamp: new Date(this.pauseStartTime),
          scrollDepth: this.lastScrollDepth,
          duration: Math.round(duration)
        });
        this.metrics.totalPauseTime += Math.round(duration);
      }
      this.pauseStartTime = 0;
    }

    // Set new timer: if no scroll event fires for 3s, mark pause as started
    // Use lastScrollTime so the pause duration includes the initial wait period
    const scrollTimeSnapshot = now;
    this.pauseTimer = setTimeout(() => {
      this.pauseStartTime = scrollTimeSnapshot; // pause started when scrolling stopped
    }, this.PAUSE_THRESHOLD_MS);
  }

  // Track when user clicks "Generate Summary"
  trackSummaryGeneration(riskScore: number, categories: string[]): void {
    this.metrics.summaryGenerated = true;
    this.metrics.summaryGeneratedAt = new Date();
    this.metrics.timeBeforeSummary = this.getElapsedSeconds();
    this.metrics.riskScore = riskScore;
    this.metrics.detectedCategories = categories;
  }

  // Track when user clicks on a highlighted clause
  trackClauseClick(category: string, position: { start: number; end: number }): void {
    this.metrics.clausesClicked.push({
      category,
      timestamp: new Date(),
      position
    });
  }

  // Track hover enter on a clause (for ai-hover condition)
  trackHoverEnter(category: string, clauseId: string): void {
    this.currentHoverStart = Date.now();
    this.currentHoverCategory = category;
    this.currentHoverClauseId = clauseId;
  }

  // Track hover leave on a clause (for ai-hover condition)
  trackHoverLeave(): void {
    if (this.currentHoverStart > 0) {
      const duration = Date.now() - this.currentHoverStart;
      // Only record hovers longer than 200ms (ignore pass-throughs)
      if (duration > 200) {
        this.metrics.hoverEvents.push({
          category: this.currentHoverCategory,
          clauseId: this.currentHoverClauseId,
          timestamp: new Date(this.currentHoverStart),
          duration
        });
      }
      this.currentHoverStart = 0;
      this.currentHoverCategory = '';
      this.currentHoverClauseId = '';
    }
  }

  // End the session and calculate final metrics
  endSession(): void {
    this.metrics.timeEnded = new Date();
    this.metrics.totalReadingTime = this.getElapsedSeconds();
    this.metrics.scrollBehavior = this.determineScrollBehavior();

    // Finalize any active pause
    if (this.pauseStartTime > 0) {
      const duration = (Date.now() - this.pauseStartTime) / 1000;
      if (duration >= this.PAUSE_THRESHOLD_MS / 1000) {
        this.metrics.pauseEvents.push({
          timestamp: new Date(this.pauseStartTime),
          scrollDepth: this.lastScrollDepth,
          duration: Math.round(duration)
        });
        this.metrics.totalPauseTime += Math.round(duration);
      }
      this.pauseStartTime = 0;
    }
    if (this.pauseTimer) {
      clearTimeout(this.pauseTimer);
    }

    // Finalize any active hover
    this.trackHoverLeave();

    // Calculate summary view duration
    if (this.metrics.summaryGenerated && this.metrics.summaryGeneratedAt) {
      this.metrics.summaryViewDuration = Math.floor(
        (this.metrics.timeEnded.getTime() - this.metrics.summaryGeneratedAt.getTime()) / 1000
      );
    }
    
    this.stopScrollTracking();
  }

  // Send metrics to backend for analysis
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
      pauseEvents: this.metrics.pauseEvents.map(p => ({
        ...p,
        timestamp: p.timestamp.toISOString()
      })),
      clausesClicked: this.metrics.clausesClicked.map(c => ({
        ...c,
        timestamp: c.timestamp.toISOString()
      })),
      hoverEvents: this.metrics.hoverEvents.map(h => ({
        ...h,
        timestamp: h.timestamp.toISOString()
      }))
    };
    
    return this.http.post(`${this.apiUrl}/metrics`, metricsToSave);
  }

  // Get current metrics (for debugging or real-time display)
  getCurrentMetrics(): UserMetrics {
    return { ...this.metrics };
  }

  getSessionId(): string {
    return this.metrics.sessionId;
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
      scrollUpCount: 0,
      reReadSections: 0,
      pauseEvents: [],
      totalPauseTime: 0,
      summaryGenerated: false,
      clausesClicked: [],
      hoverEvents: []
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

  private stopScrollTracking(): void {
    if (this.scrollTrackingInterval) {
      clearInterval(this.scrollTrackingInterval);
    }
  }
}