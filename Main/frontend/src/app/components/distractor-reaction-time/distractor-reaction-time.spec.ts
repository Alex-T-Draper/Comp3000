import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DistractorReactionTime } from './distractor-reaction-time';

describe('DistractorReactionTime', () => {
  let component: DistractorReactionTime;
  let fixture: ComponentFixture<DistractorReactionTime>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DistractorReactionTime]
    })
    .compileComponents();

    fixture = TestBed.createComponent(DistractorReactionTime);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
