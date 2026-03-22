import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TosAiHover } from './tos-ai-hover';

describe('TosAiHover', () => {
  let component: TosAiHover;
  let fixture: ComponentFixture<TosAiHover>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TosAiHover]
    })
    .compileComponents();

    fixture = TestBed.createComponent(TosAiHover);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
