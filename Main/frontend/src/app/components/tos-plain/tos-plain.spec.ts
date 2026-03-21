import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TosPlain } from './tos-plain';

describe('TosPlain', () => {
  let component: TosPlain;
  let fixture: ComponentFixture<TosPlain>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TosPlain]
    })
    .compileComponents();

    fixture = TestBed.createComponent(TosPlain);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
