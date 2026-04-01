import { ComponentFixture, TestBed } from '@angular/core/testing';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { Router } from '@angular/router';

import { TosPlainComponent } from './tos-plain';
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
  saveMetrics: vi.fn(),
};
const mockNlpApiService = {
  analyzeText: vi.fn(),
  loadTosFile: vi.fn(),
};
const mockEyeTrackingService = {
  connect: vi.fn(),
  disconnect: vi.fn(),
  startTracking: vi.fn(),
  stopTracking: vi.fn(),
  updateScrollPosition: vi.fn(),
};

describe('TosPlainComponent', () => {
  let component: TosPlainComponent;
  let fixture: ComponentFixture<TosPlainComponent>;

  beforeEach(async () => {
    vi.clearAllMocks();
    mockTrackingService.getSessionId.mockReturnValue('test-session-id');
    mockNlpApiService.loadTosFile.mockReturnValue({ subscribe: vi.fn() });
    mockTrackingService.saveMetrics.mockReturnValue({ subscribe: vi.fn() });

    TestBed.resetTestingModule();

    await TestBed.configureTestingModule({
      imports: [TosPlainComponent, HttpClientTestingModule],
      providers: [
        { provide: Router, useValue: mockRouter },
        { provide: TrackingService, useValue: mockTrackingService },
        { provide: NlpApiService, useValue: mockNlpApiService },
        { provide: EyeTrackingService, useValue: mockEyeTrackingService },
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(TosPlainComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should have correct tosId', () => {
    expect(component.tosId).toBe('plain-tos-001');
  });

  it('should call loadTosFile with ecommerce_tos on init', () => {
    expect(mockNlpApiService.loadTosFile).toHaveBeenCalledWith('ecommerce_tos');
  });

  it('should set tosText and call initializeTracking when loadTosFile succeeds', () => {
    mockNlpApiService.loadTosFile.mockReturnValue({
      subscribe: (h: any) => h.next('Sample TOS text'),
    });
    component.loadTosDocument();
    expect(component.tosText).toBe('Sample TOS text');
    expect(mockTrackingService.startSession).toHaveBeenCalledWith(
      expect.any(String),
      'plain-tos-001',
      'Sample TOS text',
      'BazaarBox Terms of Service',
      'control'
    );
    expect(mockEyeTrackingService.startTracking).toHaveBeenCalledWith('test-session-id');
  });

  it('should set error text when loadTosFile fails', () => {
    mockNlpApiService.loadTosFile.mockReturnValue({
      subscribe: (h: any) => h.error(new Error('Network error')),
    });
    component.loadTosDocument();
    expect(component.tosText).toBe('Failed to load Terms of Service. Please try again later.');
  });

  it('should call saveMetrics and navigate to /distractor-word-scramble on finishReading', () => {
    mockTrackingService.saveMetrics.mockReturnValue({
      subscribe: (h: any) => h.next(),
    });
    component.finishReading();
    expect(mockTrackingService.saveMetrics).toHaveBeenCalled();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/distractor-word-scramble']);
  });

  it('should stop eye tracking and end session on destroy', () => {
    component.ngOnDestroy();
    expect(mockEyeTrackingService.stopTracking).toHaveBeenCalledWith('test-session-id');
    expect(mockTrackingService.endSession).toHaveBeenCalled();
  });
});
