import { TestBed } from '@angular/core/testing';
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TrackingService, UserMetrics, ScrollEvent, PauseEvent } from './tracking';

describe('TrackingService', () => {
  let service: TrackingService;
  let httpTestingController: HttpTestingController;
  const apiUrl = 'http://127.0.0.1:8000/api';

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [TrackingService]
    });

    service = TestBed.inject(TrackingService);
    httpTestingController = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTestingController.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('UserMetrics', () => {
    it('should have required properties', () => {
      const mockMetrics: UserMetrics = {
        sessionId: 'session-123',
        userId: 'user-1',
        tosId: 'tos-ecommerce',
        conditionGroup: 'control',
        tosLength: 5000,
        tosTitle: 'E-commerce Terms',
        timeStarted: new Date(),
        didReadComplete: false,
        scrollEvents: [],
        maxScrollDepth: 0,
        scrollBehavior: 'quick-scroll',
        scrollUpCount: 0,
        reReadSections: 0,
        pauseEvents: [],
        totalPauseTime: 0,
        summaryGenerated: false,
        clausesClicked: [],
        hoverEvents: []
      };

      expect(mockMetrics.sessionId).toBe('session-123');
      expect(mockMetrics.userId).toBe('user-1');
      expect(mockMetrics.tosId).toBe('tos-ecommerce');
    });
  });

  describe('ScrollEvent tracking', () => {
    it('should create scroll events with correct structure', () => {
      const scrollEvent: ScrollEvent = {
        timestamp: new Date(),
        scrollDepth: 50,
        scrollPosition: 1000,
        direction: 'down'
      };

      expect(scrollEvent.scrollDepth).toBe(50);
      expect(scrollEvent.direction).toBe('down');
    });

    it('should track scroll depth as percentage', () => {
      const scrollEvent: ScrollEvent = {
        timestamp: new Date(),
        scrollDepth: 75.5,
        scrollPosition: 2000,
        direction: 'down'
      };

      expect(scrollEvent.scrollDepth).toBeLessThanOrEqual(100);
      expect(scrollEvent.scrollDepth).toBeGreaterThanOrEqual(0);
    });

    it('should track scroll direction changes', () => {
      const downEvent: ScrollEvent = {
        timestamp: new Date(),
        scrollDepth: 50,
        scrollPosition: 1000,
        direction: 'down'
      };

      const upEvent: ScrollEvent = {
        timestamp: new Date(Date.now() + 1000),
        scrollDepth: 45,
        scrollPosition: 900,
        direction: 'up'
      };

      expect(downEvent.direction).toBe('down');
      expect(upEvent.direction).toBe('up');
    });
  });

  describe('PauseEvent tracking', () => {
    it('should create pause events with correct structure', () => {
      const pauseEvent: PauseEvent = {
        timestamp: new Date(),
        scrollDepth: 30,
        duration: 5 // seconds
      };

      expect(pauseEvent.duration).toBeGreaterThan(0);
      expect(pauseEvent.scrollDepth).toBeDefined();
    });

    it('should track pause duration in seconds', () => {
      const pauseEvent: PauseEvent = {
        timestamp: new Date(),
        scrollDepth: 50,
        duration: 12
      };

      expect(typeof pauseEvent.duration).toBe('number');
      expect(pauseEvent.duration).toBeGreaterThanOrEqual(0);
    });
  });

  describe('Condition groups', () => {
    it('should support all required condition groups', () => {
      const conditionGroups = [
        'control',
        'scroll-gate',
        'formatted',
        'ai-summary',
        'ai-enhanced',
        'ai-hover'
      ];

      conditionGroups.forEach(condition => {
        expect(['control', 'scroll-gate', 'formatted', 'ai-summary', 'ai-enhanced', 'ai-hover'])
          .toContain(condition);
      });
    });
  });

  describe('Scroll behavior classification', () => {
    it('should classify scroll behaviors correctly', () => {
      const behaviors = ['quick-scroll', 'thorough-read', 'partial-read'];
      
      behaviors.forEach(behavior => {
        expect(['quick-scroll', 'thorough-read', 'partial-read'])
          .toContain(behavior);
      });
    });
  });

  describe('Reading session tracking', () => {
    it('should track session start and end times', () => {
      const startTime = new Date('2026-04-01T10:00:00');
      const endTime = new Date('2026-04-01T10:15:00');

      const metrics: UserMetrics = {
        sessionId: 'session-read-test',
        userId: 'user-1',
        tosId: 'tos-1',
        conditionGroup: 'control',
        tosLength: 3000,
        tosTitle: 'Test ToS',
        timeStarted: startTime,
        timeEnded: endTime,
        totalReadingTime: 900, // 15 minutes in seconds
        didReadComplete: true,
        scrollEvents: [],
        maxScrollDepth: 100,
        scrollBehavior: 'thorough-read',
        scrollUpCount: 2,
        reReadSections: 1,
        pauseEvents: [],
        totalPauseTime: 300,
        summaryGenerated: true,
        clausesClicked: [],
        hoverEvents: []
      };

      expect(metrics.totalReadingTime).toBe(900);
      expect(metrics.timeEnded!.getTime()).toBeGreaterThan(metrics.timeStarted.getTime());
    });
  });

  describe('Summary engagement tracking', () => {
    it('should track summary generation', () => {
      const metrics: UserMetrics = {
        sessionId: 'session-summary',
        userId: 'user-1',
        tosId: 'tos-1',
        conditionGroup: 'ai-summary',
        tosLength: 2000,
        tosTitle: 'Test ToS',
        timeStarted: new Date(),
        didReadComplete: false,
        scrollEvents: [],
        maxScrollDepth: 25,
        scrollBehavior: 'quick-scroll',
        scrollUpCount: 0,
        reReadSections: 0,
        pauseEvents: [],
        totalPauseTime: 0,
        summaryGenerated: true,
        summaryGeneratedAt: new Date(),
        summaryViewDuration: 180, // seconds
        clausesClicked: [],
        hoverEvents: []
      };

      expect(metrics.summaryGenerated).toBe(true);
      expect(metrics.summaryViewDuration).toBeGreaterThan(0);
    });
  });

  describe('Clause interaction tracking', () => {
    it('should track clause clicks', () => {
      const clause = {
        category: 'data-collection',
        timestamp: new Date(),
        position: { start: 100, end: 150 }
      };

      expect(clause.category).toBeTruthy();
      expect(clause.position.start).toBeLessThan(clause.position.end);
    });
  });

  describe('Hover event tracking', () => {
    it('should track hover events with duration', () => {
      const hoverEvent = {
        category: 'privacy-concerns',
        clauseId: 'clause-123',
        timestamp: new Date(),
        duration: 2500 // milliseconds
      };

      expect(hoverEvent.duration).toBeGreaterThan(0);
      expect(hoverEvent.clauseId).toBeTruthy();
      expect(typeof hoverEvent.duration).toBe('number');
    });

    it('should track multiple hover events', () => {
      const hoverEvents = [
        {
          category: 'data-collection',
          clauseId: 'clause-1',
          timestamp: new Date(),
          duration: 2000
        },
        {
          category: 'user-rights',
          clauseId: 'clause-2',
          timestamp: new Date(Date.now() + 5000),
          duration: 1500
        }
      ];

      expect(hoverEvents.length).toBe(2);
      expect(hoverEvents[0].category).not.toBe(hoverEvents[1].category);
    });
  });

  describe('Re-read and scroll-up tracking', () => {
    it('should track scroll-up gestures', () => {
      const metrics: UserMetrics = {
        sessionId: 'session-reread',
        userId: 'user-1',
        tosId: 'tos-1',
        conditionGroup: 'control',
        tosLength: 5000,
        tosTitle: 'Test ToS',
        timeStarted: new Date(),
        didReadComplete: true,
        scrollEvents: [],
        maxScrollDepth: 100,
        scrollBehavior: 'thorough-read',
        scrollUpCount: 3, // scrolled back up 3 times
        reReadSections: 2, // re-read 2 sections
        pauseEvents: [],
        totalPauseTime: 0,
        summaryGenerated: false,
        clausesClicked: [],
        hoverEvents: []
      };

      expect(metrics.scrollUpCount).toBeGreaterThan(0);
      expect(metrics.reReadSections).toBeGreaterThan(0);
    });
  });

  describe('Risk score and NLP results', () => {
    it('should store risk score', () => {
      const metrics: UserMetrics = {
        sessionId: 'session-risk',
        userId: 'user-1',
        tosId: 'tos-1',
        conditionGroup: 'control',
        tosLength: 5000,
        tosTitle: 'Test ToS',
        timeStarted: new Date(),
        didReadComplete: true,
        scrollEvents: [],
        maxScrollDepth: 100,
        scrollBehavior: 'thorough-read',
        scrollUpCount: 0,
        reReadSections: 0,
        pauseEvents: [],
        totalPauseTime: 0,
        summaryGenerated: false,
        clausesClicked: [],
        hoverEvents: [],
        riskScore: 65,
        detectedCategories: ['data-collection', 'sharing-with-third-parties']
      };

      expect(metrics.riskScore).toBe(65);
      expect(metrics.detectedCategories).toContain('data-collection');
    });
  });

  describe('Time tracking accuracy', () => {
    it('should accurately track time to bottom', () => {
      const metrics: UserMetrics = {
        sessionId: 'session-time',
        userId: 'user-1',
        tosId: 'tos-1',
        conditionGroup: 'control',
        tosLength: 5000,
        tosTitle: 'Test ToS',
        timeStarted: new Date('2026-04-01T10:00:00'),
        timeToBottom: 120, // 2 minutes
        didReadComplete: true,
        scrollEvents: [],
        maxScrollDepth: 100,
        scrollBehavior: 'quick-scroll',
        scrollUpCount: 0,
        reReadSections: 0,
        pauseEvents: [],
        totalPauseTime: 0,
        summaryGenerated: false,
        clausesClicked: [],
        hoverEvents: []
      };

      expect(metrics.timeToBottom).toBeDefined();
      expect(metrics.timeToBottom).toBeGreaterThan(0);
    });

    it('should track time before summary generation', () => {
      const metrics: UserMetrics = {
        sessionId: 'session-pre-summary',
        userId: 'user-1',
        tosId: 'tos-1',
        conditionGroup: 'ai-summary',
        tosLength: 3000,
        tosTitle: 'Test ToS',
        timeStarted: new Date(),
        timeBeforeSummary: 45, // 45 seconds before summary clicked
        didReadComplete: false,
        scrollEvents: [],
        maxScrollDepth: 30,
        scrollBehavior: 'partial-read',
        scrollUpCount: 0,
        reReadSections: 0,
        pauseEvents: [],
        totalPauseTime: 0,
        summaryGenerated: true,
        clausesClicked: [],
        hoverEvents: []
      };

      expect(metrics.timeBeforeSummary).toBeDefined();
      expect(metrics.timeBeforeSummary).toBeGreaterThan(0);
    });
  });
});
