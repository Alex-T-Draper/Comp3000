import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TosScrollRequired } from './tos-scroll-required';

describe('TosScrollRequired', () => {
  let component: TosScrollRequired;
  let fixture: ComponentFixture<TosScrollRequired>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TosScrollRequired]
    })
    .compileComponents();

    fixture = TestBed.createComponent(TosScrollRequired);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
