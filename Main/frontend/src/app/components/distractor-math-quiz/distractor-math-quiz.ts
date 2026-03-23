// src/app/components/distractor-math-quiz/distractor-math-quiz.ts
import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';

interface Question {
  question: string;
  options: number[];
  answer: number;
}

@Component({
  selector: 'app-distractor-math-quiz',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './distractor-math-quiz.html',
  styleUrls: ['./distractor-math-quiz.scss']
})
export class DistractorMathQuizComponent implements OnInit {
  questions: Question[] = [];
  currentIndex: number = 0;
  selectedAnswer: number | null = null;
  showFeedback: boolean = false;
  correctCount: number = 0;
  isComplete: boolean = false;
  
  timeLeft: number = 90; // 90 seconds total
  timerInterval: any;

  constructor(private router: Router, private cdr: ChangeDetectorRef) {}

  ngOnInit(): void {
    this.generateQuestions();
    this.startTimer();
  }

  /**
   * Generate 5 random math questions
   */
  generateQuestions(): void {
    this.questions = [
      this.generateAddition(),
      this.generateSubtraction(),
      this.generateMultiplication(),
      this.generatePercentage(),
      this.generateAverage()
    ];
  }

  /**
   * Generate addition question
   */
  private generateAddition(): Question {
    const a = Math.floor(Math.random() * 50) + 10;
    const b = Math.floor(Math.random() * 50) + 10;
    const answer = a + b;
    
    return {
      question: `${a} + ${b} = ?`,
      options: this.generateOptions(answer),
      answer
    };
  }

  /**
   * Generate subtraction question
   */
  private generateSubtraction(): Question {
    const a = Math.floor(Math.random() * 50) + 50;
    const b = Math.floor(Math.random() * 30) + 10;
    const answer = a - b;
    
    return {
      question: `${a} - ${b} = ?`,
      options: this.generateOptions(answer),
      answer
    };
  }

  /**
   * Generate multiplication question
   */
  private generateMultiplication(): Question {
    const a = Math.floor(Math.random() * 12) + 3;
    const b = Math.floor(Math.random() * 12) + 3;
    const answer = a * b;
    
    return {
      question: `${a} × ${b} = ?`,
      options: this.generateOptions(answer),
      answer
    };
  }

  /**
   * Generate percentage question
   */
  private generatePercentage(): Question {
    const total = Math.floor(Math.random() * 100) + 50;
    const percent = [10, 20, 25, 50][Math.floor(Math.random() * 4)];
    const answer = Math.floor((total * percent) / 100);
    
    return {
      question: `What is ${percent}% of ${total}?`,
      options: this.generateOptions(answer),
      answer
    };
  }

  /**
   * Generate average question
   */
  private generateAverage(): Question {
    const nums = [
      Math.floor(Math.random() * 30) + 60,
      Math.floor(Math.random() * 30) + 60,
      Math.floor(Math.random() * 30) + 60
    ];
    const answer = Math.floor(nums.reduce((a, b) => a + b, 0) / nums.length);
    
    return {
      question: `What is the average of ${nums[0]}, ${nums[1]}, and ${nums[2]}?`,
      options: this.generateOptions(answer),
      answer
    };
  }

  /**
   * Generate 4 answer options (1 correct, 3 wrong)
   */
  private generateOptions(correct: number): number[] {
    const options = [correct];
    
    while (options.length < 4) {
      const offset = Math.floor(Math.random() * 20) - 10;
      const wrong = correct + offset;
      if (wrong !== correct && !options.includes(wrong) && wrong > 0) {
        options.push(wrong);
      }
    }
    
    return this.shuffleArray(options);
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
   * Start countdown timer
   */
  startTimer(): void {
    this.timerInterval = setInterval(() => {
      this.timeLeft--;
      if (this.timeLeft <= 0) {
        this.timeUp();
      }
      this.cdr.markForCheck();
    }, 1000);
  }

  /**
   * Time's up - end quiz
   */
  timeUp(): void {
    clearInterval(this.timerInterval);
    this.isComplete = true;
  }

  /**
   * Select an answer
   */
  selectAnswer(answer: number): void {
    if (this.showFeedback) return;
    this.selectedAnswer = answer;
  }

  /**
   * Submit answer
   */
  submitAnswer(): void {
    if (this.selectedAnswer === null) return;
    
    if (this.selectedAnswer === this.getCurrentQuestion().answer) {
      this.correctCount++;
    }
    
    this.showFeedback = true;
    
    setTimeout(() => {
      this.nextQuestion();
      this.cdr.markForCheck();
    }, 1000);
  }

  /**
   * Move to next question
   */
  nextQuestion(): void {
    this.currentIndex++;
    this.selectedAnswer = null;
    this.showFeedback = false;
    
    if (this.currentIndex >= this.questions.length) {
      clearInterval(this.timerInterval);
      this.isComplete = true;
    }
  }

  /**
   * Continue to next condition
   */
  continue(): void {
    this.router.navigate(['/tos-ai-summary']);
  }

  /**
   * Get current question
   */
  getCurrentQuestion(): Question {
    return this.questions[this.currentIndex];
  }

  /**
   * Check if answer is correct
   */
  isCorrect(option: number): boolean {
    return option === this.getCurrentQuestion().answer;
  }

  /**
   * Get progress
   */
  getProgress(): string {
    return `${this.currentIndex + 1} / ${this.questions.length}`;
  }

  ngOnDestroy(): void {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
    }
  }
}