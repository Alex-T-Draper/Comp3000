import { ComponentFixture, TestBed } from '@angular/core/testing';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { HttpClientTestingModule } from '@angular/common/http/testing';
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

describe('TosFormattedComponent', () => {
  let component: TosFormattedComponent;
  let fixture: ComponentFixture<TosFormattedComponent>;

  beforeEach(async () => {
    TestBed.resetTestingModule();

    await TestBed.configureTestingModule({
      imports: [TosFormattedComponent, HttpClientTestingModule],
      providers: [
        { provide: Router, useValue: mockRouter },
        { provide: TrackingService, useValue: mockTrackingService },
        { provide: NlpApiService, useValue: mockNlpApiService },
        { provide: EyeTrackingService, useValue: mockEyeTrackingService },
      ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(TosFormattedComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
