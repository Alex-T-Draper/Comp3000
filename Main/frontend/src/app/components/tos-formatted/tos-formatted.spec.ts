import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TosFormatted } from './tos-formatted';

describe('TosFormatted', () => {
  let component: TosFormatted;
  let fixture: ComponentFixture<TosFormatted>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TosFormatted]
    })
    .compileComponents();

    fixture = TestBed.createComponent(TosFormatted);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
