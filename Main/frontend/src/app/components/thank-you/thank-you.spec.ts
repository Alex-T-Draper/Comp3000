import { ComponentFixture, TestBed } from '@angular/core/testing';
import { describe, it, expect, beforeEach, vi } from 'vitest';

import { ThankYouComponent } from './thank-you';

describe('ThankYouComponent', () => {
  let component: ThankYouComponent;
  let fixture: ComponentFixture<ThankYouComponent>;

  beforeEach(async () => {
    vi.clearAllMocks();
    sessionStorage.clear();
    TestBed.resetTestingModule();

    await TestBed.configureTestingModule({
      imports: [ThankYouComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(ThankYouComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should have a truthy formUrl on creation', () => {
    expect(component.formUrl).toBeTruthy();
  });

  it('should read userName from sessionStorage in ngOnInit', () => {
    sessionStorage.setItem('userName', 'TestUser');
    component.ngOnInit();
    expect(component.userName).toBe('TestUser');
  });

  it('should default userName to "Participant" when sessionStorage is empty', () => {
    sessionStorage.removeItem('userName');
    component.ngOnInit();
    expect(component.userName).toBe('Participant');
  });

  it('openFormInNewTab should call window.open with the Google Forms URL', () => {
    const openSpy = vi.spyOn(window, 'open').mockImplementation(() => null);
    component.openFormInNewTab();
    expect(openSpy).toHaveBeenCalledWith(
      expect.stringContaining('docs.google.com/forms'),
      '_blank'
    );
  });
});
