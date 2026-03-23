import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DistractorSpotDifference } from './distractor-spot-difference';

describe('DistractorSpotDifference', () => {
  let component: DistractorSpotDifference;
  let fixture: ComponentFixture<DistractorSpotDifference>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DistractorSpotDifference]
    })
    .compileComponents();

    fixture = TestBed.createComponent(DistractorSpotDifference);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
