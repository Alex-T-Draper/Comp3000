import { ComponentFixture, TestBed } from '@angular/core/testing';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { Router } from '@angular/router';

import { DistractorWordScrambleComponent } from './distractor-word-scramble';

const mockRouter = { navigate: vi.fn(), navigateByUrl: vi.fn() };

describe('DistractorWordScrambleComponent', () => {
  let component: DistractorWordScrambleComponent;
  let fixture: ComponentFixture<DistractorWordScrambleComponent>;

  beforeEach(async () => {
    vi.clearAllMocks();
    vi.useFakeTimers();
    TestBed.resetTestingModule();

    await TestBed.configureTestingModule({
      imports: [DistractorWordScrambleComponent],
      providers: [
        { provide: Router, useValue: mockRouter },
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(DistractorWordScrambleComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialise with 5 words and start at index 0', () => {
    expect(component.words.length).toBe(5);
    expect(component.currentIndex).toBe(0);
    expect(component.correctCount).toBe(0);
    expect(component.isComplete).toBe(false);
  });

  it('getCurrentWord should return the word at currentIndex', () => {
    component.currentIndex = 0;
    expect(component.getCurrentWord()).toBe(component.words[0]);
  });

  it('getProgress should return correct fraction string', () => {
    component.currentIndex = 2;
    expect(component.getProgress()).toBe('3 / 5');
  });

  it('checkAnswer should increment correctCount and set feedback for correct answer', () => {
    const currentWord = component.getCurrentWord();
    component.userAnswer = currentWord.answer;
    component.checkAnswer();
    expect(component.correctCount).toBe(1);
    expect(component.feedback).toContain('Correct');
    expect(component.showFeedback).toBe(true);
  });

  it('checkAnswer should accept answers case-insensitively', () => {
    const currentWord = component.getCurrentWord();
    component.userAnswer = currentWord.answer.toLowerCase();
    component.checkAnswer();
    expect(component.correctCount).toBe(1);
  });

  it('checkAnswer should not increment correctCount for wrong answer', () => {
    component.userAnswer = 'WRONGANSWER';
    component.checkAnswer();
    expect(component.correctCount).toBe(0);
    expect(component.feedback).toContain(component.words[0].answer);
    expect(component.showFeedback).toBe(true);
  });

  it('nextWord should advance index and clear state', () => {
    component.userAnswer = 'something';
    component.feedback = 'Correct!';
    component.showFeedback = true;
    component.nextWord();
    expect(component.currentIndex).toBe(1);
    expect(component.userAnswer).toBe('');
    expect(component.showFeedback).toBe(false);
    expect(component.feedback).toBe('');
  });

  it('nextWord should set isComplete when past last word', () => {
    component.currentIndex = component.words.length - 1;
    component.nextWord();
    expect(component.isComplete).toBe(true);
  });

  it('checkAnswer with fake timers should advance to next word after 1 second', () => {
    const currentWord = component.getCurrentWord();
    component.userAnswer = currentWord.answer;
    component.checkAnswer();
    expect(component.currentIndex).toBe(0); // not yet advanced
    vi.advanceTimersByTime(1000);
    expect(component.currentIndex).toBe(1); // now advanced
  });

  it('continue should navigate to /tos-scroll-required', () => {
    component.continue();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/tos-scroll-required']);
  });
});
