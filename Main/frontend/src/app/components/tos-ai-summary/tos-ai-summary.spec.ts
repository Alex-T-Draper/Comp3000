import { ComponentFixture, TestBed } from '@angular/core/testing';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { Router } from '@angular/router';

import { TosAiSummaryComponent } from './tos-ai-summary';
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

describe('TosAiSummaryComponent', () => {
  let component: TosAiSummaryComponent;
  let fixture: ComponentFixture<TosAiSummaryComponent>;

  beforeEach(async () => {
    vi.clearAllMocks();
    mockTrackingService.getSessionId.mockReturnValue('test-session-id');
    mockNlpApiService.loadTosFile.mockReturnValue({ subscribe: vi.fn() });
    mockNlpApiService.analyzeTos.mockReturnValue({ subscribe: vi.fn() });
    mockTrackingService.saveMetrics.mockReturnValue({ subscribe: vi.fn() });

    TestBed.resetTestingModule();

    await TestBed.configureTestingModule({
      imports: [TosAiSummaryComponent, HttpClientTestingModule],
      providers: [
        { provide: Router, useValue: mockRouter },
        { provide: TrackingService, useValue: mockTrackingService },
        { provide: NlpApiService, useValue: mockNlpApiService },
        { provide: EyeTrackingService, useValue: mockEyeTrackingService },
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(TosAiSummaryComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should have correct tosId', () => {
    expect(component.tosId).toBe('ai-summary-tos-004');
  });

  it('should call loadTosFile with education_tos on init', () => {
    expect(mockNlpApiService.loadTosFile).toHaveBeenCalledWith('education_tos');
  });

  it('should set analysis and summaryGenerated on generateSummary success', () => {
    const mockResponse = {
      risk: { normalized_percent: 45 },
      grouped_clauses: { 'data-sharing': {} },
    };
    mockNlpApiService.analyzeTos.mockReturnValue({
      subscribe: (h: any) => h.next(mockResponse),
    });
    component.generateSummary();
    expect(component.analysis).toEqual(mockResponse);
    expect(component.summaryGenerated).toBe(true);
    expect(component.isLoading).toBe(false);
  });

  it('should call trackSummaryGeneration after generateSummary success', () => {
    const mockResponse = {
      risk: { normalized_percent: 75 },
      grouped_clauses: { 'category-a': {}, 'category-b': {} },
    };
    mockNlpApiService.analyzeTos.mockReturnValue({
      subscribe: (h: any) => h.next(mockResponse),
    });
    component.generateSummary();
    expect(mockTrackingService.trackSummaryGeneration).toHaveBeenCalledWith(
      75,
      ['category-a', 'category-b']
    );
  });

  it('should set error and clear isLoading on generateSummary failure', () => {
    mockNlpApiService.analyzeTos.mockReturnValue({
      subscribe: (h: any) => h.error(new Error('API error')),
    });
    component.generateSummary();
    expect(component.error).toBe('Failed to generate summary. Please try again.');
    expect(component.isLoading).toBe(false);
    expect(component.summaryGenerated).toBe(false);
  });

  it('getRiskLevel should return high for score >= 60', () => {
    expect(component.getRiskLevel(60)).toBe('high');
    expect(component.getRiskLevel(85)).toBe('high');
  });

  it('getRiskLevel should return medium for score 30-59', () => {
    expect(component.getRiskLevel(30)).toBe('medium');
    expect(component.getRiskLevel(59)).toBe('medium');
  });

  it('getRiskLevel should return low for score < 30', () => {
    expect(component.getRiskLevel(0)).toBe('low');
    expect(component.getRiskLevel(29)).toBe('low');
  });

  it('getSeverityColor should return correct colours', () => {
    expect(component.getSeverityColor('high')).toBe('red');
    expect(component.getSeverityColor('medium')).toBe('orange');
    expect(component.getSeverityColor('low')).toBe('green');
    expect(component.getSeverityColor('unknown')).toBe('gray');
  });

  it('getRiskDescription should return high-risk message for score >= 60', () => {
    expect(component.getRiskDescription(60)).toContain('high-risk');
  });

  it('getRiskDescription should return moderate message for score 30-59', () => {
    expect(component.getRiskDescription(30)).toContain('moderate');
  });

  it('getRiskDescription should return low-risk message for score < 30', () => {
    expect(component.getRiskDescription(29)).toContain('low risk');
  });

  it('should call saveMetrics and navigate to /distractor-reaction-time on finishReading', () => {
    mockTrackingService.saveMetrics.mockReturnValue({
      subscribe: (h: any) => h.next(),
    });
    component.finishReading();
    expect(mockTrackingService.saveMetrics).toHaveBeenCalled();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/distractor-reaction-time']);
  });

  it('should stop eye tracking and end session on destroy', () => {
    component.ngOnDestroy();
    expect(mockEyeTrackingService.stopTracking).toHaveBeenCalledWith('test-session-id');
    expect(mockTrackingService.endSession).toHaveBeenCalled();
  });
});
