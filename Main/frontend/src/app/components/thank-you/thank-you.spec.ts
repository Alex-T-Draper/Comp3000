import { ComponentFixture, TestBed } from '@angular/core/testing';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { Router } from '@angular/router';

import { ThankYouComponent } from './thank-you';
import { TrackingService } from '../../services/tracking';
import { NlpApiService } from '../../services/nlp-api';
import { EyeTrackingService } from '../../services/eye-tracking';

const mockRouter = { navigate: vi.fn(), navigateByUrl: vi.fn() };
const mockTrackingService = { startTracking: vi.fn(), recordUserMetrics: vi.fn() };
const mockNlpApiService = { analyzeText: vi.fn() };
const mockEyeTrackingService = { connect: vi.fn(), disconnect: vi.fn() };

describe('ThankYouComponent', () => {
  let component: ThankYouComponent;
  let fixture: ComponentFixture<ThankYouComponent>;

  beforeEach(async () => {
    TestBed.resetTestingModule();

    await TestBed.configureTestingModule({
      imports: [ThankYouComponent, HttpClientTestingModule],
      providers: [
        { provide: Router, useValue: mockRouter },
        { provide: TrackingService, useValue: mockTrackingService },
        { provide: NlpApiService, useValue: mockNlpApiService },
        { provide: EyeTrackingService, useValue: mockEyeTrackingService },
      ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ThankYouComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
