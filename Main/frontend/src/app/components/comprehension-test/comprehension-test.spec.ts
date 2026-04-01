import { ComponentFixture, TestBed } from '@angular/core/testing';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { Router } from '@angular/router';

import { ComprehensionTestComponent } from './comprehension-test';

const mockRouter = { navigate: vi.fn(), navigateByUrl: vi.fn() };

describe('ComprehensionTestComponent', () => {
  let component: ComprehensionTestComponent;
  let fixture: ComponentFixture<ComprehensionTestComponent>;

  beforeEach(async () => {
    vi.clearAllMocks();
    TestBed.resetTestingModule();

    await TestBed.configureTestingModule({
      imports: [ComprehensionTestComponent, HttpClientTestingModule],
      providers: [
        { provide: Router, useValue: mockRouter },
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(ComprehensionTestComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should start in intro section', () => {
    expect(component.currentSection).toBe('intro');
  });

  it('should have 18 recognition questions and 5 confidence questions', () => {
    expect(component.recognitionQuestions.length).toBe(18);
    expect(component.confidenceQuestions.length).toBe(5);
  });

  it('startTest should switch section to recognition', () => {
    component.startTest();
    expect(component.currentSection).toBe('recognition');
  });

  it('answerRecognition should record answer and advance index', () => {
    component.startTest();
    const firstId = component.recognitionQuestions[0].id;
    component.answerRecognition('true');
    expect(component.recognitionQuestions.find(q => q.id === firstId)!.userAnswer).toBe('true');
    expect(component.currentRecognitionIndex).toBe(1);
  });

  it('answerRecognition on last question should switch to confidence section', () => {
    component.startTest();
    for (let i = 0; i < 17; i++) {
      component.answerRecognition('false');
    }
    expect(component.currentSection).toBe('recognition');
    component.answerRecognition('true');
    expect(component.currentSection).toBe('confidence');
  });

  it('answerConfidence should record answer and advance index', () => {
    component.currentSection = 'confidence';
    component.answerConfidence(4);
    expect(component.confidenceQuestions[0].userAnswer).toBe(4);
    expect(component.currentConfidenceIndex).toBe(1);
  });

  it('answerConfidence on last question should set section to complete', () => {
    component.currentSection = 'confidence';
    for (let i = 0; i < 4; i++) {
      component.answerConfidence(3);
    }
    component.answerConfidence(5);
    expect(component.currentSection).toBe('complete');
  });

  it('calculateRecognitionScore should return 100 when all answers are correct', () => {
    component.recognitionQuestions.forEach(q => {
      q.userAnswer = q.isTrue ? 'true' : 'false';
    });
    expect(component.calculateRecognitionScore()).toBe(100);
  });

  it('calculateRecognitionScore should return 0 when all answers are wrong', () => {
    component.recognitionQuestions.forEach(q => {
      q.userAnswer = q.isTrue ? 'false' : 'true';
    });
    expect(component.calculateRecognitionScore()).toBe(0);
  });

  it('calculateRecognitionScore should exclude unsure answers', () => {
    component.recognitionQuestions.forEach(q => {
      q.userAnswer = 'unsure';
    });
    expect(component.calculateRecognitionScore()).toBe(0);
  });

  it('calculateAverageConfidence should compute average of answered questions', () => {
    component.confidenceQuestions[0].userAnswer = 2;
    component.confidenceQuestions[1].userAnswer = 4;
    component.confidenceQuestions[2].userAnswer = null;
    component.confidenceQuestions[3].userAnswer = null;
    component.confidenceQuestions[4].userAnswer = null;
    expect(component.calculateAverageConfidence()).toBe(3);
  });

  it('calculateAverageConfidence should return 0 when no answers', () => {
    component.confidenceQuestions.forEach(q => (q.userAnswer = null));
    expect(component.calculateAverageConfidence()).toBe(0);
  });

  it('getRecognitionProgress should return correct fraction string', () => {
    component.currentRecognitionIndex = 3;
    expect(component.getRecognitionProgress()).toBe('4 / 18');
  });

  it('getConfidenceProgress should return correct fraction string', () => {
    component.currentConfidenceIndex = 2;
    expect(component.getConfidenceProgress()).toBe('3 / 5');
  });

  it('continue should navigate to /thank-you', () => {
    component.continue();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/thank-you']);
  });
});
