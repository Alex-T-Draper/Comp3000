import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DistractorMathQuiz } from './distractor-math-quiz';

describe('DistractorMathQuiz', () => {
  let component: DistractorMathQuiz;
  let fixture: ComponentFixture<DistractorMathQuiz>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DistractorMathQuiz]
    })
    .compileComponents();

    fixture = TestBed.createComponent(DistractorMathQuiz);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
