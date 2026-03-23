// src/app/components/distractor-pattern-match/distractor-pattern-match.ts
import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';

interface Cell {
  color: string;
  selected: boolean;
}

@Component({
  selector: 'app-distractor-pattern-match',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './distractor-pattern-match.html',
  styleUrls: ['./distractor-pattern-match.scss']
})
export class DistractorPatternMatchComponent implements OnInit {
  // Cloud/tech themed colors
  colors = ['#4285F4', '#34A853', '#FBBC05', '#EA4335', '#9E9E9E']; // Google Cloud colors
  
  grid: Cell[][] = [];
  pattern: string[][] = [];
  
  currentRound: number = 1;
  totalRounds: number = 3;
  
  phase: 'memorize' | 'recall' | 'feedback' | 'complete' = 'memorize';
  countdown: number = 3;
  
  score: number = 0;
  countdownInterval: any;
  selectedColor: string = '';

  constructor(private router: Router, private cdr: ChangeDetectorRef) {}

  ngOnInit(): void {
    this.startRound();
  }

  /**
   * Start a new round
   */
  startRound(): void {
    this.phase = 'memorize';
    this.countdown = 3;
    this.selectedColor = '';
    this.generatePattern();
    this.initializeGrid();
    
    // Start countdown
    this.countdownInterval = setInterval(() => {
      this.countdown--;
      if (this.countdown === 0) {
        clearInterval(this.countdownInterval);
        this.phase = 'recall';
      }
      this.cdr.markForCheck();
    }, 1000);
  }

  /**
   * Generate random pattern
   */
  generatePattern(): void {
    this.pattern = [];
    for (let i = 0; i < 3; i++) {
      const row: string[] = [];
      for (let j = 0; j < 3; j++) {
        row.push(this.colors[Math.floor(Math.random() * this.colors.length)]);
      }
      this.pattern.push(row);
    }
  }

  /**
   * Initialize empty grid for recall
   */
  initializeGrid(): void {
    this.grid = [];
    for (let i = 0; i < 3; i++) {
      const row: Cell[] = [];
      for (let j = 0; j < 3; j++) {
        row.push({ color: '#FFFFFF', selected: false });
      }
      this.grid.push(row);
    }
  }

  /**
   * Handle cell click during recall phase
   */
  selectColor(color: string): void {
    this.selectedColor = color;
  }

  fillCell(row: number, col: number): void {
    if (this.phase !== 'recall' || !this.selectedColor) return;
    this.grid[row][col].color = this.selectedColor;
    this.grid[row][col].selected = true;
  }

  /**
   * Check if cell is correct
   */
  isCellCorrect(row: number, col: number): boolean {
    return this.grid[row][col].color === this.pattern[row][col];
  }

  /**
   * Submit answer
   */
  submitAnswer(): void {
    let correct = 0;
    for (let i = 0; i < 3; i++) {
      for (let j = 0; j < 3; j++) {
        if (this.isCellCorrect(i, j)) {
          correct++;
        }
      }
    }
    
    this.score += correct;
    this.phase = 'feedback';
    
    // Move to next round after 2 seconds
    setTimeout(() => {
      if (this.currentRound < this.totalRounds) {
        this.currentRound++;
        this.startRound();
      } else {
        this.phase = 'complete';
      }
      this.cdr.markForCheck();
    }, 2000);
  }

  /**
   * Check if all cells are selected
   */
  allCellsSelected(): boolean {
    return this.grid.every(row => row.every(cell => cell.selected));
  }

  /**
   * Continue to next condition
   */
  continue(): void {
    this.router.navigate(['/tos-formatted']);
  }

  /**
   * Get percentage score
   */
  getScorePercentage(): number {
    return Math.round((this.score / (this.totalRounds * 9)) * 100);
  }

  ngOnDestroy(): void {
    if (this.countdownInterval) {
      clearInterval(this.countdownInterval);
    }
  }
}