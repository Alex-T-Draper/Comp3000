import { ComponentFixture, TestBed } from '@angular/core/testing';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { Router } from '@angular/router';

import { DistractorWordScrambleComponent } from './distractor-word-scramble';
import { TrackingService } from '../../services/tracking';
import { NlpApiService } from '../../services/nlp-api';
import { EyeTrackingService } from '../../services/eye-tracking';

const mockRouter = { navigate: vi.fn(), navigateByUrl: vi.fn() };
const mockTrackingService = { startTracking: vi.fn(), recordUserMetrics: vi.fn() };
const mockNlpApiService = { analyzeText: vi.fn() };
const mockEyeTrackingService = { connect: vi.fn(), disconnect: vi.fn() };

describe('DistractorWordScrambleComponent', () => {
  let component: DistractorWordScrambleComponent;
  let fixture: ComponentFixture<DistractorWordScrambleComponent>;

  beforeEach(async () => {
    TestBed.resetTestingModule();
    await TestBed.configureTestingModule({
      imports: [DistractorWordScrambleComponent, HttpClientTestingModule],
      providers: [
        { provide: Router, useValue: mockRouter },
        { provide: TrackingService, useValue: mockTrackingService },
        { provide: NlpApiService, useValue: mockNlpApiService },
        { provide: EyeTrackingService, useValue: mockEyeTrackingService },
      ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(DistractorWordScrambleComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
