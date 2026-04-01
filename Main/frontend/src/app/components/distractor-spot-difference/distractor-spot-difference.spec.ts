import { ComponentFixture, TestBed } from '@angular/core/testing';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { Router } from '@angular/router';

import { DistractorSpotDifferenceComponent } from './distractor-spot-difference';
import { TrackingService } from '../../services/tracking';
import { NlpApiService } from '../../services/nlp-api';
import { EyeTrackingService } from '../../services/eye-tracking';

const mockRouter = { navigate: vi.fn(), navigateByUrl: vi.fn() };
const mockTrackingService = { startTracking: vi.fn(), recordUserMetrics: vi.fn() };
const mockNlpApiService = { analyzeText: vi.fn() };
const mockEyeTrackingService = { connect: vi.fn(), disconnect: vi.fn() };

describe('DistractorSpotDifferenceComponent', () => {
  let component: DistractorSpotDifferenceComponent;
  let fixture: ComponentFixture<DistractorSpotDifferenceComponent>;

  beforeEach(async () => {
    TestBed.resetTestingModule();
    await TestBed.configureTestingModule({
      imports: [DistractorSpotDifferenceComponent, HttpClientTestingModule],
      providers: [
        { provide: Router, useValue: mockRouter },
        { provide: TrackingService, useValue: mockTrackingService },
        { provide: NlpApiService, useValue: mockNlpApiService },
        { provide: EyeTrackingService, useValue: mockEyeTrackingService },
      ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(DistractorSpotDifferenceComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
