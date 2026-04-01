import { ComponentFixture, TestBed } from '@angular/core/testing';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { Router } from '@angular/router';

import { DistractorSpotDifferenceComponent } from './distractor-spot-difference';

const mockRouter = { navigate: vi.fn(), navigateByUrl: vi.fn() };

describe('DistractorSpotDifferenceComponent', () => {
  let component: DistractorSpotDifferenceComponent;
  let fixture: ComponentFixture<DistractorSpotDifferenceComponent>;

  beforeEach(async () => {
    vi.clearAllMocks();
    vi.useFakeTimers();
    TestBed.resetTestingModule();

    await TestBed.configureTestingModule({
      imports: [DistractorSpotDifferenceComponent],
      providers: [
        { provide: Router, useValue: mockRouter },
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(DistractorSpotDifferenceComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
    // Stop auto-running timer
    clearInterval(component.timerInterval);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialise with 5 differences and 60 seconds', () => {
    expect(component.differences.length).toBe(5);
    expect(component.timeLeft).toBe(60);
    expect(component.foundCount).toBe(0);
    expect(component.isComplete).toBe(false);
  });

  it('handleClick should mark a nearby difference as found', () => {
    const diff = component.differences[0];
    diff.found = false;
    component.isComplete = false;

    const mockElement = {
      getBoundingClientRect: () => ({ left: 0, top: 0, width: 100, height: 100 }),
    } as unknown as HTMLElement;

    const mockEvent = {
      currentTarget: mockElement,
      clientX: diff.x,   // percentage mapped directly since width=100
      clientY: diff.y,
    } as unknown as MouseEvent;

    component.handleClick(mockEvent, 1);
    expect(diff.found).toBe(true);
    expect(component.foundCount).toBe(1);
  });

  it('handleClick should set clickedWrong when clicking away from differences', () => {
    component.differences.forEach(d => (d.found = true)); // mark all found so none match
    // Reset foundCount but keep found=true so clicks don't match
    component.differences.forEach(d => (d.found = true));
    component.isComplete = false;

    const mockElement = {
      getBoundingClientRect: () => ({ left: 0, top: 0, width: 100, height: 100 }),
    } as unknown as HTMLElement;
    // All differences are already found so any click is "wrong"
    const mockEvent = {
      currentTarget: mockElement,
      clientX: 50,
      clientY: 50,
    } as unknown as MouseEvent;

    // Create unfound difference far away so click doesn't match
    component.differences.forEach(d => (d.found = false));
    component.differences[0].x = 90;
    component.differences[0].y = 90;
    component.differences[1].x = 80;
    component.differences[1].y = 80;
    component.differences[2].x = 70;
    component.differences[2].y = 70;
    component.differences[3].x = 60;
    component.differences[3].y = 60;
    component.differences[4].x = 55;
    component.differences[4].y = 55;

    const missEvent = {
      currentTarget: mockElement,
      clientX: 1,  // far from all differences
      clientY: 1,
    } as unknown as MouseEvent;

    component.handleClick(missEvent, 1);
    expect(component.clickedWrong).toBe(true);
  });

  it('handleClick should do nothing when isComplete', () => {
    component.isComplete = true;
    const diff = component.differences[0];
    diff.found = false;

    const mockElement = {
      getBoundingClientRect: () => ({ left: 0, top: 0, width: 100, height: 100 }),
    } as unknown as HTMLElement;
    const mockEvent = {
      currentTarget: mockElement,
      clientX: diff.x,
      clientY: diff.y,
    } as unknown as MouseEvent;

    component.handleClick(mockEvent, 1);
    expect(diff.found).toBe(false);
  });

  it('endGame should set isComplete to true', () => {
    component.endGame();
    expect(component.isComplete).toBe(true);
  });

  it('getSuccessMessage should return perfect message when all found', () => {
    component.foundCount = component.totalDifferences;
    expect(component.getSuccessMessage()).toContain('Perfect');
  });

  it('getSuccessMessage should return good job message when >= 3 found', () => {
    component.foundCount = 3;
    component.totalDifferences = 5;
    expect(component.getSuccessMessage()).toContain('Good job');
  });

  it('getSuccessMessage should return nice try message when < 3 found', () => {
    component.foundCount = 1;
    component.totalDifferences = 5;
    expect(component.getSuccessMessage()).toContain('Nice try');
  });

  it('continue should navigate to /tos-ai-hover', () => {
    component.continue();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/tos-ai-hover']);
  });
});
