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
};
const mockNlpApiService = {
  analyzeText: vi.fn(),
  loadTosFile: vi.fn().mockReturnValue({ subscribe: vi.fn() }),
};
const mockEyeTrackingService = {
  connect: vi.fn(),
  disconnect: vi.fn(),
  startTracking: vi.fn(),
  stopTracking: vi.fn(),
};

describe('TosAiSummaryComponent', () => {
  let component: TosAiSummaryComponent;
  let fixture: ComponentFixture<TosAiSummaryComponent>;

  beforeEach(async () => {
    TestBed.resetTestingModule();

    await TestBed.configureTestingModule({
      imports: [TosAiSummaryComponent, HttpClientTestingModule],
      providers: [
        { provide: Router, useValue: mockRouter },
        { provide: TrackingService, useValue: mockTrackingService },
        { provide: NlpApiService, useValue: mockNlpApiService },
        { provide: EyeTrackingService, useValue: mockEyeTrackingService },
      ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(TosAiSummaryComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
