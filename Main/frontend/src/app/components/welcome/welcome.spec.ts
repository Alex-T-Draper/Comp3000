import { ComponentFixture, TestBed } from '@angular/core/testing';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { Router } from '@angular/router';

import { WelcomeComponent } from './welcome';

const mockRouter = { navigate: vi.fn(), navigateByUrl: vi.fn() };

describe('WelcomeComponent', () => {
  let component: WelcomeComponent;
  let fixture: ComponentFixture<WelcomeComponent>;
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    vi.clearAllMocks();
    TestBed.resetTestingModule();

    await TestBed.configureTestingModule({
      imports: [WelcomeComponent, HttpClientTestingModule],
      providers: [
        { provide: Router, useValue: mockRouter },
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(WelcomeComponent);
    component = fixture.componentInstance;
    httpMock = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialise with empty state', () => {
    expect(component.userName).toBe('');
    expect(component.isLoading).toBe(false);
    expect(component.error).toBeNull();
  });

  it('should set error when name is empty', () => {
    component.userName = '';
    component.startStudy();
    expect(component.error).toBe('Please enter your name to continue.');
    expect(component.isLoading).toBe(false);
  });

  it('should set error when name is blank whitespace', () => {
    component.userName = '   ';
    component.startStudy();
    expect(component.error).toBe('Please enter your name to continue.');
  });

  it('should set error when name is less than 2 characters', () => {
    component.userName = 'A';
    component.startStudy();
    expect(component.error).toBe('Name must be at least 2 characters.');
  });

  it('should set isLoading true and clear error when valid name submitted', () => {
    component.error = 'Previous error';
    component.userName = 'Alice';
    component.startStudy();
    expect(component.isLoading).toBe(true);
    expect(component.error).toBeNull();
    httpMock.expectOne('http://127.0.0.1:8000/api/users').flush({ userId: '123' });
  });

  it('should POST to /api/users with trimmed name', () => {
    component.userName = '  Alice  ';
    component.startStudy();
    const req = httpMock.expectOne('http://127.0.0.1:8000/api/users');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ name: 'Alice' });
    req.flush({ userId: '1' });
  });

  it('should store userName and userId in sessionStorage on success', () => {
    component.userName = 'Alice';
    component.startStudy();
    const req = httpMock.expectOne('http://127.0.0.1:8000/api/users');
    req.flush({ userId: '456' });
    expect(sessionStorage.getItem('userName')).toBe('Alice');
    expect(sessionStorage.getItem('userId')).toBe('456');
  });

  it('should navigate to /tos-plain on successful user creation', () => {
    component.userName = 'Alice';
    component.startStudy();
    const req = httpMock.expectOne('http://127.0.0.1:8000/api/users');
    req.flush({ userId: '123' });
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/tos-plain']);
  });

  it('should set duplicate error and clear name on 400 "already exists"', () => {
    component.userName = 'Alice';
    component.startStudy();
    const req = httpMock.expectOne('http://127.0.0.1:8000/api/users');
    req.flush({ detail: 'Name already exists' }, { status: 400, statusText: 'Bad Request' });
    expect(component.error).toBe('This name is already taken. Please choose a different name.');
    expect(component.isLoading).toBe(false);
    expect(component.userName).toBe('');
  });

  it('should set api detail message as error when non-duplicate error detail present', () => {
    component.userName = 'Alice';
    component.startStudy();
    const req = httpMock.expectOne('http://127.0.0.1:8000/api/users');
    req.flush({ detail: 'Custom server message' }, { status: 422, statusText: 'Unprocessable' });
    expect(component.error).toBe('Custom server message');
    expect(component.isLoading).toBe(false);
  });

  it('should set generic error on server error without detail', () => {
    component.userName = 'Alice';
    component.startStudy();
    const req = httpMock.expectOne('http://127.0.0.1:8000/api/users');
    req.flush({}, { status: 500, statusText: 'Server Error' });
    expect(component.error).toBe('Failed to start study. Please try again.');
    expect(component.isLoading).toBe(false);
  });

  it('should call startStudy when Enter key is pressed', () => {
    component.userName = 'Alice';
    const spy = vi.spyOn(component, 'startStudy');
    component.onKeyPress(new KeyboardEvent('keypress', { key: 'Enter' }));
    expect(spy).toHaveBeenCalled();
    httpMock.expectOne('http://127.0.0.1:8000/api/users').flush({ userId: '1' });
  });

  it('should not call startStudy for non-Enter keys', () => {
    const spy = vi.spyOn(component, 'startStudy');
    component.onKeyPress(new KeyboardEvent('keypress', { key: 'a' }));
    expect(spy).not.toHaveBeenCalled();
  });
});
