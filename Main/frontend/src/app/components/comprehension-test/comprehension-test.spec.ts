import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ComprehensionTest } from './comprehension-test';

describe('ComprehensionTest', () => {
  let component: ComprehensionTest;
  let fixture: ComponentFixture<ComprehensionTest>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ComprehensionTest]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ComprehensionTest);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
