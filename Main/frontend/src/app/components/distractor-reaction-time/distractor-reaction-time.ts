// src/app/components/distractor-reaction-time/distractor-reaction-time.ts
import { Component, OnInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';

@Component({
  selector: 'app-distractor-reaction-time',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './distractor-reaction-time.html',
  styleUrls: ['./distractor-reaction-time.scss']
})
export class DistractorReactionTimeComponent implements OnInit, OnDestroy {
  // Study-themed words
  targetWords = ['READ', 'STUDY', 'LEARN', 'FOCUS', 'THINK'];
  distractorWords = ['SLEEP', 'PLAY', 'WALK', 'EAT', 'TALK', 'REST', 'SWIM'];
  
  currentWord: string = '';
  isTargetWord: boolean = false;
  
  score: number = 0;
  misses: number = 0;
  falseAlarms: number = 0;
  
  phase: 'instructions' | 'playing' | 'complete' = 'instructions';
  
  roundsCompleted: number = 0;
  totalRounds: number = 30;
  
  gameInterval: any;
  
  // Timing
  wordDisplayDuration: number = 800; // ms
  betweenWordDelay: number = 600; // ms

  constructor(private router: Router, private cdr: ChangeDetectorRef) {}

  ngOnInit(): void {
    // Listen for spacebar
    document.addEventListener('keydown', this.handleKeyPress);
  }

  ngOnDestroy(): void {
    document.removeEventListener('keydown', this.handleKeyPress);
    if (this.gameInterval) {
      clearInterval(this.gameInterval);
    }
  }

  /**
   * Start the game
   */
  startGame(): void {
    this.phase = 'playing';
    this.score = 0;
    this.misses = 0;
    this.falseAlarms = 0;
    this.roundsCompleted = 0;
    
    this.showNextWord();
  }

  /**
   * Show next word
   */
  showNextWord(): void {
    if (this.roundsCompleted >= this.totalRounds) {
      this.endGame();
      return;
    }

    // Randomly choose target or distractor (50/50)
    this.isTargetWord = Math.random() < 0.5;
    
    if (this.isTargetWord) {
      this.currentWord = this.targetWords[Math.floor(Math.random() * this.targetWords.length)];
    } else {
      this.currentWord = this.distractorWords[Math.floor(Math.random() * this.distractorWords.length)];
    }

    // Track if user pressed space during this word
    let userPressed = false;
    
    // Show word for specified duration
    setTimeout(() => {
      // Check if user should have pressed but didn't (miss)
      if (this.isTargetWord && !userPressed) {
        this.misses++;
      }
      
      this.currentWord = '';
      this.roundsCompleted++;
      this.cdr.markForCheck();
      
      // Delay before next word
      setTimeout(() => {
        this.showNextWord();
        this.cdr.markForCheck();
      }, this.betweenWordDelay);
    }, this.wordDisplayDuration);

    // Handle spacebar press during word display
    const pressHandler = (e: KeyboardEvent) => {
      if (e.code === 'Space' && this.currentWord !== '') {
        userPressed = true;
        
        if (this.isTargetWord) {
          this.score++;
        } else {
          this.falseAlarms++;
        }
      }
    };

    document.addEventListener('keydown', pressHandler, { once: true });
  }

  /**
   * Handle keypress
   */
  handleKeyPress = (e: KeyboardEvent): void => {
    if (e.code === 'Space' && this.phase === 'playing' && this.currentWord !== '') {
      e.preventDefault();
      // Scoring is handled in showNextWord
    }
  }

  /**
   * End the game
   */
  endGame(): void {
    this.phase = 'complete';
    if (this.gameInterval) {
      clearInterval(this.gameInterval);
    }
    this.cdr.markForCheck();
  }

  /**
   * Continue to next condition
   */
  continue(): void {
    this.router.navigate(['/tos-ai-enhanced']);
  }

  /**
   * Get accuracy percentage
   */
  getAccuracy(): number {
    const totalTargets = this.score + this.misses;
    if (totalTargets === 0) return 0;
    return Math.round((this.score / totalTargets) * 100);
  }

  /**
   * Get progress percentage
   */
  getProgress(): number {
    return Math.round((this.roundsCompleted / this.totalRounds) * 100);
  }
}