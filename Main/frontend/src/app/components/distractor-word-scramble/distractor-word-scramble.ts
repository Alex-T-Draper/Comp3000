// src/app/components/distractor-word-scramble/distractor-word-scramble.ts
import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

interface Word {
  scrambled: string;
  answer: string;
}

@Component({
  selector: 'app-distractor-word-scramble',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './distractor-word-scramble.html',
  styleUrls: ['./distractor-word-scramble.scss']
})
export class DistractorWordScrambleComponent implements OnInit {
  words: Word[] = [
    { scrambled: 'HECKOTUC', answer: 'CHECKOUT' },
    { scrambled: 'YPATMEN', answer: 'PAYMENT' },
    { scrambled: 'LIVDEERY', answer: 'DELIVERY' },
    { scrambled: 'FURNDE', answer: 'REFUND' },
    { scrambled: 'SIDCOUNT', answer: 'DISCOUNT' }
  ];

  currentIndex: number = 0;
  userAnswer: string = '';
  feedback: string = '';
  showFeedback: boolean = false;
  correctCount: number = 0;
  isComplete: boolean = false;

  constructor(private router: Router, private cdr: ChangeDetectorRef) {}

  ngOnInit(): void {
    // Shuffle words for variety
    this.words = this.shuffleArray(this.words);
  }

  /**
   * Check the user's answer
   */
  checkAnswer(): void {
    const correct = this.userAnswer.toUpperCase().trim() === this.words[this.currentIndex].answer;
    
    if (correct) {
      this.correctCount++;
      this.feedback = '✓ Correct!';
    } else {
      this.feedback = `✗ The answer was: ${this.words[this.currentIndex].answer}`;
    }

    this.showFeedback = true;

    // Move to next word after 1 second
    setTimeout(() => {
      this.nextWord();
      this.cdr.markForCheck();
    }, 1000);
  }

  /**
   * Move to next word
   */
  nextWord(): void {
    this.currentIndex++;
    this.userAnswer = '';
    this.showFeedback = false;
    this.feedback = '';

    if (this.currentIndex >= this.words.length) {
      this.isComplete = true;
    }
  }

  /**
   * Continue to next condition
   */
  continue(): void {
    this.router.navigate(['/tos-scroll-required']);
  }

  /**
   * Shuffle array
   */
  private shuffleArray<T>(array: T[]): T[] {
    const shuffled = [...array];
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
  }

  /**
   * Get current word
   */
  getCurrentWord(): Word {
    return this.words[this.currentIndex];
  }

  /**
   * Get progress
   */
  getProgress(): string {
    return `${this.currentIndex + 1} / ${this.words.length}`;
  }
}