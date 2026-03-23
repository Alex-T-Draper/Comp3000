import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DistractorPatternMatch } from './distractor-pattern-match';

describe('DistractorPatternMatch', () => {
  let component: DistractorPatternMatch;
  let fixture: ComponentFixture<DistractorPatternMatch>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DistractorPatternMatch]
    })
    .compileComponents();

    fixture = TestBed.createComponent(DistractorPatternMatch);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
