import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TosViewer } from './tos-ai-enhanced';

describe('TosViewer', () => {
  let component: TosViewer;
  let fixture: ComponentFixture<TosViewer>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TosViewer]
    })
    .compileComponents();

    fixture = TestBed.createComponent(TosViewer);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
