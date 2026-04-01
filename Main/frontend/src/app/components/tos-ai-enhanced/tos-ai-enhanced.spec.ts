import { ComponentFixture, TestBed } from '@angular/core/testing';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { Router } from '@angular/router';

import { TosAiEnhancedComponent } from './tos-ai-enhanced';
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

describe('TosAiEnhancedComponent', () => {
  let component: TosAiEnhancedComponent;
  let fixture: ComponentFixture<TosAiEnhancedComponent>;

  beforeEach(async () => {
    vi.clearAllMocks();
    mockTrackingService.getSessionId.mockReturnValue('test-session-id');
    mockNlpApiService.loadTosFile.mockReturnValue({ subscribe: vi.fn() });
    mockNlpApiService.analyzeTos.mockReturnValue({ subscribe: vi.fn() });
    mockTrackingService.saveMetrics.mockReturnValue({ subscribe: vi.fn() });

    TestBed.resetTestingModule();

    await TestBed.configureTestingModule({
      imports: [TosAiEnhancedComponent, HttpClientTestingModule],
      providers: [
        { provide: Router, useValue: mockRouter },
        { provide: TrackingService, useValue: mockTrackingService },
        { provide: NlpApiService, useValue: mockNlpApiService },
        { provide: EyeTrackingService, useValue: mockEyeTrackingService },
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(TosAiEnhancedComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should call loadTosFile with fitness_tos on init', () => {
    expect(mockNlpApiService.loadTosFile).toHaveBeenCalledWith('fitness_tos');
  });

  it('should set analysis and summaryGenerated on generateSummary success', () => {
    const mockResponse = {
      risk: { normalized_percent: 72 },
      grouped_clauses: {},
    };
    mockNlpApiService.analyzeTos.mockReturnValue({
      subscribe: (h: any) => h.next(mockResponse),
    });
    component.generateSummary();
    expect(component.analysis).toEqual(mockResponse);
    expect(component.summaryGenerated).toBe(true);
    expect(component.showSummary).toBe(true);
    expect(component.isLoading).toBe(false);
  });

  it('should call trackSummaryGeneration after generateSummary success', () => {
    const mockResponse = {
      risk: { normalized_percent: 72 },
      grouped_clauses: {},
    };
    mockNlpApiService.analyzeTos.mockReturnValue({
      subscribe: (h: any) => h.next(mockResponse),
    });
    component.generateSummary();
    expect(mockTrackingService.trackSummaryGeneration).toHaveBeenCalledWith(72, []);
  });

  it('should set error on generateSummary failure', () => {
    mockNlpApiService.analyzeTos.mockReturnValue({
      subscribe: (h: any) => h.error(new Error('fail')),
    });
    component.generateSummary();
    expect(component.error).toBe('Failed to generate summary. Please try again.');
    expect(component.isLoading).toBe(false);
  });

  it('getRiskLevel should return high for score >= 60', () => {
    expect(component.getRiskLevel(60)).toBe('high');
    expect(component.getRiskLevel(100)).toBe('high');
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
    expect(component.getSeverityColor('other')).toBe('gray');
  });

  it('getRiskDescription should reference high-risk for score >= 60', () => {
    expect(component.getRiskDescription(60)).toContain('high-risk');
  });

  it('getRiskDescription should reference moderate for score 30-59', () => {
    expect(component.getRiskDescription(30)).toContain('moderate');
  });

  it('getRiskDescription should reference low risk for score < 30', () => {
    expect(component.getRiskDescription(10)).toContain('low risk');
  });

  it('proceedToNextPhase should call saveMetrics and navigate to /distractor-spot-difference', () => {
    mockTrackingService.saveMetrics.mockReturnValue({
      subscribe: (h: any) => h.next(),
    });
    component.proceedToNextPhase();
    expect(mockTrackingService.saveMetrics).toHaveBeenCalled();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/distractor-spot-difference']);
  });

  it('should stop eye tracking and end session on destroy', () => {
    component.ngOnDestroy();
    expect(mockEyeTrackingService.stopTracking).toHaveBeenCalledWith('test-session-id');
    expect(mockTrackingService.endSession).toHaveBeenCalled();
  });
});
