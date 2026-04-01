import { ComponentFixture, TestBed } from '@angular/core/testing';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { DomSanitizer } from '@angular/platform-browser';
import { Router } from '@angular/router';

import { TosFormattedComponent } from './tos-formatted';
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

describe('TosFormattedComponent', () => {
  let component: TosFormattedComponent;
  let fixture: ComponentFixture<TosFormattedComponent>;

  beforeEach(async () => {
    vi.clearAllMocks();
    mockTrackingService.getSessionId.mockReturnValue('test-session-id');
    mockNlpApiService.loadTosFile.mockReturnValue({ subscribe: vi.fn() });
    mockTrackingService.saveMetrics.mockReturnValue({ subscribe: vi.fn() });

    TestBed.resetTestingModule();

    await TestBed.configureTestingModule({
      imports: [TosFormattedComponent, HttpClientTestingModule],
      providers: [
        { provide: Router, useValue: mockRouter },
        { provide: TrackingService, useValue: mockTrackingService },
        { provide: NlpApiService, useValue: mockNlpApiService },
        { provide: EyeTrackingService, useValue: mockEyeTrackingService },
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(TosFormattedComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should have correct tosId', () => {
    expect(component.tosId).toBe('formatted-tos-003');
  });

  it('should call loadTosFile with socialmedia_tos on init', () => {
    expect(mockNlpApiService.loadTosFile).toHaveBeenCalledWith('socialmedia_tos');
  });

  it('should wrap high-risk keywords in highlight-high spans', () => {
    const sanitizer = TestBed.inject(DomSanitizer);
    const spy = vi.spyOn(sanitizer, 'bypassSecurityTrustHtml').mockReturnValue('' as any);
    component.tosText = 'We may share your data with third parties.';
    component.applyFormatting();
    const html: string = spy.mock.calls[0][0] as string;
    expect(html).toContain('highlight-high');
  });

  it('should wrap medium-risk keywords in highlight-medium spans', () => {
    const sanitizer = TestBed.inject(DomSanitizer);
    const spy = vi.spyOn(sanitizer, 'bypassSecurityTrustHtml').mockReturnValue('' as any);
    component.tosText = 'We use cookies and payment information.';
    component.applyFormatting();
    const html: string = spy.mock.calls[0][0] as string;
    expect(html).toContain('highlight-medium');
  });

  it('should wrap bold keywords in bold-important strong tags', () => {
    const sanitizer = TestBed.inject(DomSanitizer);
    const spy = vi.spyOn(sanitizer, 'bypassSecurityTrustHtml').mockReturnValue('' as any);
    component.tosText = 'You agree to our terms.';
    component.applyFormatting();
    const html: string = spy.mock.calls[0][0] as string;
    expect(html).toContain('bold-important');
  });

  it('should escape HTML characters to prevent injection', () => {
    const sanitizer = TestBed.inject(DomSanitizer);
    const spy = vi.spyOn(sanitizer, 'bypassSecurityTrustHtml').mockReturnValue('' as any);
    component.tosText = '<script>alert("xss")</script>';
    component.applyFormatting();
    const html: string = spy.mock.calls[0][0] as string;
    expect(html).not.toContain('<script>');
    expect(html).toContain('&lt;script&gt;');
  });

  it('escapeRegex should escape special regex characters', () => {
    const escaped = (component as any).escapeRegex('a.b+c?d*');
    expect(escaped).toBe('a\\.b\\+c\\?d\\*');
  });

  it('should call saveMetrics and navigate to /distractor-math-quiz on finishReading', () => {
    mockTrackingService.saveMetrics.mockReturnValue({
      subscribe: (h: any) => h.next(),
    });
    component.finishReading();
    expect(mockTrackingService.saveMetrics).toHaveBeenCalled();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/distractor-math-quiz']);
  });

  it('should stop eye tracking and end session on destroy', () => {
    component.ngOnDestroy();
    expect(mockEyeTrackingService.stopTracking).toHaveBeenCalledWith('test-session-id');
    expect(mockTrackingService.endSession).toHaveBeenCalled();
  });
});
