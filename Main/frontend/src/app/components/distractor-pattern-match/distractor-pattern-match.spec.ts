import { ComponentFixture, TestBed } from '@angular/core/testing';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { Router } from '@angular/router';

import { DistractorPatternMatchComponent } from './distractor-pattern-match';

const mockRouter = { navigate: vi.fn(), navigateByUrl: vi.fn() };

describe('DistractorPatternMatchComponent', () => {
  let component: DistractorPatternMatchComponent;
  let fixture: ComponentFixture<DistractorPatternMatchComponent>;

  beforeEach(async () => {
    vi.clearAllMocks();
    vi.useFakeTimers();
    TestBed.resetTestingModule();

    await TestBed.configureTestingModule({
      imports: [DistractorPatternMatchComponent],
      providers: [
        { provide: Router, useValue: mockRouter },
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(DistractorPatternMatchComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
    // Stop the auto-running countdown from ngOnInit
    clearInterval(component.countdownInterval);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should start in memorize phase', () => {
    expect(component.phase).toBe('memorize');
  });

  it('generatePattern should create a 3x3 grid of valid colours', () => {
    component.generatePattern();
    expect(component.pattern.length).toBe(3);
    component.pattern.forEach(row => {
      expect(row.length).toBe(3);
      row.forEach(colour => {
        expect(component.colors).toContain(colour);
      });
    });
  });

  it('initializeGrid should create a 3x3 grid of white unselected cells', () => {
    component.initializeGrid();
    expect(component.grid.length).toBe(3);
    component.grid.forEach(row => {
      expect(row.length).toBe(3);
      row.forEach(cell => {
        expect(cell.color).toBe('#FFFFFF');
        expect(cell.selected).toBe(false);
      });
    });
  });

  it('selectColor should set selectedColor', () => {
    component.selectColor('#4285F4');
    expect(component.selectedColor).toBe('#4285F4');
  });

  it('fillCell should update cell colour and selected when phase is recall', () => {
    component.phase = 'recall';
    component.selectedColor = '#4285F4';
    component.fillCell(0, 0);
    expect(component.grid[0][0].color).toBe('#4285F4');
    expect(component.grid[0][0].selected).toBe(true);
  });

  it('fillCell should do nothing when phase is not recall', () => {
    component.phase = 'memorize';
    component.selectedColor = '#4285F4';
    component.fillCell(0, 0);
    expect(component.grid[0][0].color).toBe('#FFFFFF');
  });

  it('fillCell should do nothing when no colour selected', () => {
    component.phase = 'recall';
    component.selectedColor = '';
    component.fillCell(0, 0);
    expect(component.grid[0][0].color).toBe('#FFFFFF');
  });

  it('isCellCorrect should return true when grid cell matches pattern', () => {
    component.pattern[0][0] = '#4285F4';
    component.grid[0][0].color = '#4285F4';
    expect(component.isCellCorrect(0, 0)).toBe(true);
  });

  it('isCellCorrect should return false when cell does not match pattern', () => {
    component.pattern[0][0] = '#4285F4';
    component.grid[0][0].color = '#EA4335';
    expect(component.isCellCorrect(0, 0)).toBe(false);
  });

  it('allCellsSelected should return true when all cells are selected', () => {
    component.grid.forEach(row => row.forEach(cell => (cell.selected = true)));
    expect(component.allCellsSelected()).toBe(true);
  });

  it('allCellsSelected should return false when at least one cell not selected', () => {
    expect(component.allCellsSelected()).toBe(false);
  });

  it('submitAnswer should add correct cell count to score and set phase to feedback', () => {
    // Make all cells correct
    for (let i = 0; i < 3; i++) {
      for (let j = 0; j < 3; j++) {
        component.grid[i][j].color = component.pattern[i][j];
      }
    }
    component.submitAnswer();
    expect(component.score).toBe(9);
    expect(component.phase).toBe('feedback');
  });

  it('getScorePercentage should compute (score / (rounds * 9)) * 100', () => {
    component.score = 18; // 18 correct out of 27 total (3 rounds × 9 cells)
    expect(component.getScorePercentage()).toBe(67);
  });

  it('continue should navigate to /tos-formatted', () => {
    component.continue();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/tos-formatted']);
  });
});
