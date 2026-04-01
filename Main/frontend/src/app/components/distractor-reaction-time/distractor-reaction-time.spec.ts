import { ComponentFixture, TestBed } from '@angular/core/testing';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { Router } from '@angular/router';

import { DistractorReactionTimeComponent } from './distractor-reaction-time';

const mockRouter = { navigate: vi.fn(), navigateByUrl: vi.fn() };

describe('DistractorReactionTimeComponent', () => {
  let component: DistractorReactionTimeComponent;
  let fixture: ComponentFixture<DistractorReactionTimeComponent>;

  beforeEach(async () => {
    vi.clearAllMocks();
    vi.useFakeTimers();
    TestBed.resetTestingModule();

    await TestBed.configureTestingModule({
      imports: [DistractorReactionTimeComponent],
      providers: [
        { provide: Router, useValue: mockRouter },
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(DistractorReactionTimeComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  afterEach(() => {
    vi.useRealTimers();
    component.ngOnDestroy();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should start in instructions phase', () => {
    expect(component.phase).toBe('instructions');
  });

  it('startGame should switch to playing phase and reset counters', () => {
    component.score = 5;
    component.misses = 3;
    component.falseAlarms = 2;
    component.roundsCompleted = 10;
    // Prevent full showNextWord execution
    vi.spyOn(component, 'showNextWord').mockImplementation(() => {});
    component.startGame();
    expect(component.phase).toBe('playing');
    expect(component.score).toBe(0);
    expect(component.misses).toBe(0);
    expect(component.falseAlarms).toBe(0);
    expect(component.roundsCompleted).toBe(0);
  });

  it('endGame should set phase to complete', () => {
    component.endGame();
    expect(component.phase).toBe('complete');
  });

  it('getAccuracy should return 0 when no targets encountered', () => {
    component.score = 0;
    component.misses = 0;
    expect(component.getAccuracy()).toBe(0);
  });

  it('getAccuracy should calculate (score / (score + misses)) * 100', () => {
    component.score = 3;
    component.misses = 1;
    expect(component.getAccuracy()).toBe(75);
  });

  it('getAccuracy should return 100 when all targets hit', () => {
    component.score = 5;
    component.misses = 0;
    expect(component.getAccuracy()).toBe(100);
  });

  it('getProgress should return (roundsCompleted / totalRounds) * 100', () => {
    component.roundsCompleted = 15;
    component.totalRounds = 30;
    expect(component.getProgress()).toBe(50);
  });

  it('getProgress should return 0 when no rounds completed', () => {
    component.roundsCompleted = 0;
    expect(component.getProgress()).toBe(0);
  });

  it('continue should navigate to /tos-ai-enhanced', () => {
    component.continue();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/tos-ai-enhanced']);
  });
});
