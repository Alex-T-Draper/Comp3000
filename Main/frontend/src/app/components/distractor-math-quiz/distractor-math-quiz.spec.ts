import { ComponentFixture, TestBed } from '@angular/core/testing';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { Router } from '@angular/router';

import { DistractorMathQuizComponent } from './distractor-math-quiz';

const mockRouter = { navigate: vi.fn(), navigateByUrl: vi.fn() };

describe('DistractorMathQuizComponent', () => {
  let component: DistractorMathQuizComponent;
  let fixture: ComponentFixture<DistractorMathQuizComponent>;

  beforeEach(async () => {
    vi.clearAllMocks();
    vi.useFakeTimers();
    TestBed.resetTestingModule();

    await TestBed.configureTestingModule({
      imports: [DistractorMathQuizComponent],
      providers: [
        { provide: Router, useValue: mockRouter },
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(DistractorMathQuizComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
    // Stop the auto-running timer from ngOnInit to avoid side effects
    clearInterval(component.timerInterval);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should generate 5 questions on init', () => {
    expect(component.questions.length).toBe(5);
  });

  it('each question should have exactly 4 options', () => {
    component.questions.forEach(q => {
      expect(q.options.length).toBe(4);
    });
  });

  it('each question should include the correct answer in its options', () => {
    component.questions.forEach(q => {
      expect(q.options).toContain(q.answer);
    });
  });

  it('should start with timeLeft at 90', () => {
    expect(component.timeLeft).toBe(90);
  });

  it('selectAnswer should set selectedAnswer', () => {
    component.selectAnswer(42);
    expect(component.selectedAnswer).toBe(42);
  });

  it('selectAnswer should not change selectedAnswer when showFeedback is true', () => {
    component.showFeedback = true;
    component.selectAnswer(99);
    expect(component.selectedAnswer).toBeNull();
  });

  it('submitAnswer should increment correctCount when answer is correct', () => {
    const q = component.questions[0];
    component.selectedAnswer = q.answer;
    component.submitAnswer();
    expect(component.correctCount).toBe(1);
    expect(component.showFeedback).toBe(true);
  });

  it('submitAnswer should not increment correctCount when answer is wrong', () => {
    const q = component.questions[0];
    component.selectedAnswer = q.answer + 999;
    component.submitAnswer();
    expect(component.correctCount).toBe(0);
    expect(component.showFeedback).toBe(true);
  });

  it('submitAnswer should do nothing when selectedAnswer is null', () => {
    component.selectedAnswer = null;
    component.submitAnswer();
    expect(component.showFeedback).toBe(false);
  });

  it('nextQuestion should set isComplete after all questions answered', () => {
    component.currentIndex = component.questions.length - 1;
    component.nextQuestion();
    expect(component.isComplete).toBe(true);
  });

  it('isCorrect should return true for the correct option', () => {
    const q = component.questions[0];
    expect(component.isCorrect(q.answer)).toBe(true);
  });

  it('isCorrect should return false for wrong option', () => {
    const q = component.questions[0];
    expect(component.isCorrect(q.answer + 999)).toBe(false);
  });

  it('getProgress should return correct fraction string', () => {
    component.currentIndex = 2;
    expect(component.getProgress()).toBe('3 / 5');
  });

  it('timeUp should set isComplete to true and clear timer', () => {
    component.timeUp();
    expect(component.isComplete).toBe(true);
  });

  it('continue should navigate to /tos-ai-summary', () => {
    component.continue();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/tos-ai-summary']);
  });
});
