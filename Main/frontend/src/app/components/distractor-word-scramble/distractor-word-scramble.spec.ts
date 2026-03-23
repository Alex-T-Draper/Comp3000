import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DistractorWordScramble } from './distractor-word-scramble';

describe('DistractorWordScramble', () => {
  let component: DistractorWordScramble;
  let fixture: ComponentFixture<DistractorWordScramble>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DistractorWordScramble]
    })
    .compileComponents();

    fixture = TestBed.createComponent(DistractorWordScramble);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
