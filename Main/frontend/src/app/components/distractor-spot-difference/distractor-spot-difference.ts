// src/app/components/distractor-spot-difference/distractor-spot-difference.ts
import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';

interface Difference {
  id: number;
  x: number; // percentage
  y: number; // percentage
  found: boolean;
}

@Component({
  selector: 'app-distractor-spot-difference',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './distractor-spot-difference.html',
  styleUrls: ['./distractor-spot-difference.scss']
})
export class DistractorSpotDifferenceComponent implements OnInit {
  differences: Difference[] = [
    { id: 1, x: 25, y: 20, found: false },   // Play button icon (cx=75, cy=80)
    { id: 2, x: 80, y: 17.5, found: false },  // Heart icon color (~240, 70)
    { id: 3, x: 50, y: 32.5, found: false },  // Song title text (150, 130)
    { id: 4, x: 50, y: 70, found: false },    // Progress bar position (~150, 280)
    { id: 5, x: 63, y: 85.5, found: false }   // Volume slider (~190, 342)
  ];

  foundCount: number = 0;
  totalDifferences: number = 5;
  
  timeLeft: number = 60;
  timerInterval: any;
  
  isComplete: boolean = false;
  clickedWrong: boolean = false;

  constructor(private router: Router, private cdr: ChangeDetectorRef) {}

  ngOnInit(): void {
    this.startTimer();
  }

  /**
   * Start countdown timer
   */
  startTimer(): void {
    this.timerInterval = setInterval(() => {
      this.timeLeft--;
      if (this.timeLeft <= 0) {
        this.endGame();
      }
      this.cdr.markForCheck();
    }, 1000);
  }

  /**
   * Handle click on image
   */
  handleClick(event: MouseEvent, imageNumber: 1 | 2): void {
    if (this.isComplete) return;

    const target = event.currentTarget as HTMLElement;
    const rect = target.getBoundingClientRect();
    
    const x = ((event.clientX - rect.left) / rect.width) * 100;
    const y = ((event.clientY - rect.top) / rect.height) * 100;

    // Check if click is near any unfound difference
    const clickedDifference = this.differences.find(diff => {
      if (diff.found) return false;
      
      const distance = Math.sqrt(
        Math.pow(diff.x - x, 2) + Math.pow(diff.y - y, 2)
      );
      
      return distance < 10; // Within 10% radius
    });

    if (clickedDifference) {
      clickedDifference.found = true;
      this.foundCount++;
      
      if (this.foundCount === this.totalDifferences) {
        this.endGame();
      }
    } else {
      // Wrong click - show brief feedback
      this.clickedWrong = true;
      setTimeout(() => {
        this.clickedWrong = false;
        this.cdr.markForCheck();
      }, 300);
    }
  }

  /**
   * End the game
   */
  endGame(): void {
    clearInterval(this.timerInterval);
    this.isComplete = true;
  }

  /**
   * Continue to next condition
   */
  continue(): void {
    this.router.navigate(['/tos-ai-hover']);
  }

  /**
   * Get success message
   */
  getSuccessMessage(): string {
    if (this.foundCount === this.totalDifferences) {
      return 'Perfect! You found all differences! 🎉';
    } else if (this.foundCount >= 3) {
      return 'Good job! You found most of them! 👍';
    } else {
      return 'Nice try! Those were tricky! 😊';
    }
  }

  ngOnDestroy(): void {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
    }
  }
}