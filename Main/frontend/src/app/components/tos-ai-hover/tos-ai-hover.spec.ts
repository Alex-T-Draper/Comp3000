import { ComponentFixture, TestBed } from '@angular/core/testing';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { Router } from '@angular/router';

import { TosAiHoverComponent } from './tos-ai-hover';
import { TrackingService } from '../../services/tracking';
import { NlpApiService } from '../../services/nlp-api';
import { EyeTrackingService } from '../../services/eye-tracking';

const mockRouter = { navigate: vi.fn(), navigateByUrl: vi.fn() };
const mockTrackingService = {
  startTracking: vi.fn(),
  recordUserMetrics: vi.fn(),
  getSessionId: vi.fn().mockReturnValue('test-session-id'),
  startSession: vi.fn(),
  endSession: vi.fn(),
  trackScroll: vi.fn(),
  trackSummaryGeneration: vi.fn(),
  saveMetrics: vi.fn(),
};
const mockNlpApiService = {
  analyzeText: vi.fn(),
  loadTosFile: vi.fn(),
  analyzeTos: vi.fn(),
};
const mockEyeTrackingService = {
  connect: vi.fn(),
  disconnect: vi.fn(),
  startTracking: vi.fn(),
  stopTracking: vi.fn(),
  updateScrollPosition: vi.fn(),
};

describe('TosAiHoverComponent', () => {
  let component: TosAiHoverComponent;
  let fixture: ComponentFixture<TosAiHoverComponent>;

  beforeEach(async () => {
    vi.clearAllMocks();
    mockTrackingService.getSessionId.mockReturnValue('test-session-id');
    mockNlpApiService.loadTosFile.mockReturnValue({ subscribe: vi.fn() });
    mockNlpApiService.analyzeTos.mockReturnValue({ subscribe: vi.fn() });
    mockTrackingService.saveMetrics.mockReturnValue({ subscribe: vi.fn() });

    TestBed.resetTestingModule();

    await TestBed.configureTestingModule({
      imports: [TosAiHoverComponent, HttpClientTestingModule],
      providers: [
        { provide: Router, useValue: mockRouter },
        { provide: TrackingService, useValue: mockTrackingService },
        { provide: NlpApiService, useValue: mockNlpApiService },
        { provide: EyeTrackingService, useValue: mockEyeTrackingService },
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(TosAiHoverComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should have correct tosId', () => {
    expect(component.tosId).toBe('ai-hover-tos-006');
  });

  it('should call loadTosFile with musicstreaming_tos on init', () => {
    expect(mockNlpApiService.loadTosFile).toHaveBeenCalledWith('musicstreaming_tos');
  });

  it('should set analysis and summaryGenerated on generateSummary success', () => {
    const mockResponse = {
      risk: { normalized_percent: 50 },
      grouped_clauses: {},
    };
    mockNlpApiService.analyzeTos.mockReturnValue({
      subscribe: (h: any) => h.next(mockResponse),
    });
    component.generateSummary();
    expect(component.analysis).toEqual(mockResponse);
    expect(component.summaryGenerated).toBe(true);
    expect(component.isLoading).toBe(false);
  });

  it('should set error on generateSummary failure', () => {
    mockNlpApiService.analyzeTos.mockReturnValue({
      subscribe: (h: any) => h.error(new Error('API error')),
    });
    component.generateSummary();
    expect(component.error).toBe('Failed to generate summary. Please try again.');
    expect(component.isLoading).toBe(false);
  });

  it('tooltip should be null initially', () => {
    expect(component.tooltip).toBeNull();
  });

  it('getRiskLevel should return high for score >= 60', () => {
    expect(component.getRiskLevel(60)).toBe('high');
  });

  it('getRiskLevel should return medium for score 30-59', () => {
    expect(component.getRiskLevel(45)).toBe('medium');
  });

  it('getRiskLevel should return low for score < 30', () => {
    expect(component.getRiskLevel(10)).toBe('low');
  });

  it('getSeverityColor should return correct colours', () => {
    expect(component.getSeverityColor('high')).toBe('red');
    expect(component.getSeverityColor('medium')).toBe('orange');
    expect(component.getSeverityColor('low')).toBe('green');
    expect(component.getSeverityColor('unknown')).toBe('gray');
  });

  it('getRiskDescription should reference high-risk for score >= 60', () => {
    expect(component.getRiskDescription(65)).toContain('high-risk');
  });

  it('getRiskDescription should reference moderate for score 30-59', () => {
    expect(component.getRiskDescription(30)).toContain('moderate');
  });

  it('getRiskDescription should reference low risk for score < 30', () => {
    expect(component.getRiskDescription(5)).toContain('low risk');
  });

  it('finishReading should call saveMetrics and navigate to /comprehension-test', () => {
    mockTrackingService.saveMetrics.mockReturnValue({
      subscribe: (h: any) => h.next(),
    });
    component.finishReading();
    expect(mockTrackingService.saveMetrics).toHaveBeenCalled();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/comprehension-test']);
  });

  it('should stop eye tracking and end session on destroy', () => {
    component.ngOnDestroy();
    expect(mockEyeTrackingService.stopTracking).toHaveBeenCalledWith('test-session-id');
    expect(mockTrackingService.endSession).toHaveBeenCalled();
  });
});
