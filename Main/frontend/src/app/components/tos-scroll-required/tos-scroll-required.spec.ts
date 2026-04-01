import { ComponentFixture, TestBed } from '@angular/core/testing';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { Router } from '@angular/router';

import { TosScrollRequiredComponent } from './tos-scroll-required';
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

describe('TosScrollRequiredComponent', () => {
  let component: TosScrollRequiredComponent;
  let fixture: ComponentFixture<TosScrollRequiredComponent>;

  beforeEach(async () => {
    vi.clearAllMocks();
    mockTrackingService.getSessionId.mockReturnValue('test-session-id');
    mockNlpApiService.loadTosFile.mockReturnValue({ subscribe: vi.fn() });
    mockTrackingService.saveMetrics.mockReturnValue({ subscribe: vi.fn() });

    TestBed.resetTestingModule();

    await TestBed.configureTestingModule({
      imports: [TosScrollRequiredComponent, HttpClientTestingModule],
      providers: [
        { provide: Router, useValue: mockRouter },
        { provide: TrackingService, useValue: mockTrackingService },
        { provide: NlpApiService, useValue: mockNlpApiService },
        { provide: EyeTrackingService, useValue: mockEyeTrackingService },
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(TosScrollRequiredComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should have correct tosId', () => {
    expect(component.tosId).toBe('scroll-required-tos-002');
  });

  it('should initialise hasScrolledToBottom as false', () => {
    expect(component.hasScrolledToBottom).toBe(false);
  });

  it('canProceed should return false initially', () => {
    expect(component.canProceed()).toBe(false);
  });

  it('canProceed should return true when hasScrolledToBottom is true', () => {
    component.hasScrolledToBottom = true;
    expect(component.canProceed()).toBe(true);
  });

  it('should call loadTosFile with cloudstorage_tos on init', () => {
    expect(mockNlpApiService.loadTosFile).toHaveBeenCalledWith('cloudstorage_tos');
  });

  it('should set tosText on successful load', () => {
    mockNlpApiService.loadTosFile.mockReturnValue({
      subscribe: (h: any) => h.next('Cloud TOS text'),
    });
    component.loadTosDocument();
    expect(component.tosText).toBe('Cloud TOS text');
  });

  it('should set error text when loadTosFile fails', () => {
    mockNlpApiService.loadTosFile.mockReturnValue({
      subscribe: (h: any) => h.error(new Error('fail')),
    });
    component.loadTosDocument();
    expect(component.tosText).toBe('Failed to load Terms of Service. Please try again later.');
  });

  it('finishReading should alert and not navigate when !canProceed', () => {
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {});
    component.hasScrolledToBottom = false;
    component.finishReading();
    expect(alertSpy).toHaveBeenCalled();
    expect(mockRouter.navigate).not.toHaveBeenCalled();
  });

  it('finishReading should call saveMetrics and navigate to /distractor-pattern-match when canProceed', () => {
    mockTrackingService.saveMetrics.mockReturnValue({
      subscribe: (h: any) => h.next(),
    });
    component.hasScrolledToBottom = true;
    component.finishReading();
    expect(mockTrackingService.saveMetrics).toHaveBeenCalled();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/distractor-pattern-match']);
  });

  it('should stop eye tracking and end session on destroy', () => {
    component.ngOnDestroy();
    expect(mockEyeTrackingService.stopTracking).toHaveBeenCalledWith('test-session-id');
    expect(mockTrackingService.endSession).toHaveBeenCalled();
  });
});
