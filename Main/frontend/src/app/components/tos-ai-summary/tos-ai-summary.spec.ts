import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TosAiSummary } from './tos-ai-summary';

describe('TosAiSummary', () => {
  let component: TosAiSummary;
  let fixture: ComponentFixture<TosAiSummary>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TosAiSummary]
    })
    .compileComponents();

    fixture = TestBed.createComponent(TosAiSummary);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
