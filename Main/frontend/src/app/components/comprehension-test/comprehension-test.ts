// src/app/components/comprehension-test/comprehension-test.ts
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';

interface RecognitionQuestion {
  id: number;
  statement: string;
  isTrue: boolean; // Whether the statement was actually in the ToS
  tosSource: string; // Which ToS document this is from
  userAnswer: 'true' | 'false' | 'unsure' | null;
}

interface ConfidenceQuestion {
  id: number;
  question: string;
  userAnswer: number | null; // 1-5 scale
}

@Component({
  selector: 'app-comprehension-test',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './comprehension-test.html',
  styleUrls: ['./comprehension-test.scss']
})
export class ComprehensionTestComponent implements OnInit {
  userName: string = '';
  currentSection: 'intro' | 'recognition' | 'confidence' | 'complete' = 'intro';
  
  // Recognition questions (mix of true and false statements)
  recognitionQuestions: RecognitionQuestion[] = [
    {
      id: 1,
      statement: 'The company may share your information with third-party service providers.',
      isTrue: true,
      tosSource: 'multiple',
      userAnswer: null
    },
    {
      id: 2,
      statement: 'You can get a full refund at any time, even after using the service for months.',
      isTrue: false,
      tosSource: 'multiple',
      userAnswer: null
    },
    {
      id: 3,
      statement: 'The company is not liable for any indirect or consequential damages.',
      isTrue: true,
      tosSource: 'multiple',
      userAnswer: null
    },
    {
      id: 4,
      statement: 'Your subscription will automatically renew unless you cancel.',
      isTrue: true,
      tosSource: 'multiple',
      userAnswer: null
    },
    {
      id: 5,
      statement: 'The company guarantees 100% uptime and will compensate you for any downtime.',
      isTrue: false,
      tosSource: 'multiple',
      userAnswer: null
    },
    {
      id: 6,
      statement: 'You retain full ownership of content you upload.',
      isTrue: true,
      tosSource: 'multiple',
      userAnswer: null
    },
    {
      id: 7,
      statement: 'The company can change the terms at any time without notifying you.',
      isTrue: false,
      tosSource: 'multiple',
      userAnswer: null
    },
    {
      id: 8,
      statement: 'The service is provided "as is" without warranties.',
      isTrue: true,
      tosSource: 'multiple',
      userAnswer: null
    },
    {
      id: 9,
      statement: 'ConnectSphere retains your personal data for up to 3 years after you delete your account.',
      isTrue: true,
      tosSource: 'socialmedia',
      userAnswer: null
    },
    {
      id: 10,
      statement: 'VaultDrive stores your data exclusively in UK and European Economic Area data centres.',
      isTrue: true,
      tosSource: 'cloudstorage',
      userAnswer: null
    },
    {
      id: 11,
      statement: 'BazaarBox charges sellers a transaction fee of 10% on every sale.',
      isTrue: false,
      tosSource: 'ecommerce',
      userAnswer: null
    },
    {
      id: 12,
      statement: 'SonicWave requires you to connect to the internet at least every 30 days to keep offline downloads.',
      isTrue: true,
      tosSource: 'musicstreaming',
      userAnswer: null
    },
    {
      id: 13,
      statement: 'PulseFit may sell your health data to insurance companies.',
      isTrue: false,
      tosSource: 'fitness',
      userAnswer: null
    },
    {
      id: 14,
      statement: 'LearnVault certificates are equivalent to formal academic credits.',
      isTrue: false,
      tosSource: 'education',
      userAnswer: null
    },
    {
      id: 15,
      statement: 'ConnectSphere users waive their right to participate in class action lawsuits.',
      isTrue: true,
      tosSource: 'socialmedia',
      userAnswer: null
    },
    {
      id: 16,
      statement: 'LearnVault offers a full refund within 14 days if you have completed less than 25% of a course.',
      isTrue: true,
      tosSource: 'education',
      userAnswer: null
    }
  ];

  // Confidence questions
  confidenceQuestions: ConfidenceQuestion[] = [
    {
      id: 1,
      question: 'How confident are you that you understand what data the companies can collect?',
      userAnswer: null
    },
    {
      id: 2,
      question: 'Could you explain the refund policies to someone else?',
      userAnswer: null
    },
    {
      id: 3,
      question: 'Do you feel you understood the high-risk clauses (liability, data sharing, etc.)?',
      userAnswer: null
    },
    {
      id: 4,
      question: 'How well do you understand what happens if you violate the terms?',
      userAnswer: null
    },
    {
      id: 5,
      question: 'Overall, how informed do you feel about what you agreed to?',
      userAnswer: null
    }
  ];

  currentRecognitionIndex: number = 0;
  currentConfidenceIndex: number = 0;

  constructor(
    private router: Router,
    private http: HttpClient
  ) {}

  ngOnInit(): void {
    this.userName = sessionStorage.getItem('userName') || 'anonymous';
    // Shuffle recognition questions
    this.recognitionQuestions = this.shuffleArray(this.recognitionQuestions);
  }

  /**
   * Start the test
   */
  startTest(): void {
    this.currentSection = 'recognition';
  }

  /**
   * Answer recognition question
   */
  answerRecognition(answer: 'true' | 'false' | 'unsure'): void {
    this.recognitionQuestions[this.currentRecognitionIndex].userAnswer = answer;
    
    if (this.currentRecognitionIndex < this.recognitionQuestions.length - 1) {
      this.currentRecognitionIndex++;
    } else {
      // Move to confidence questions
      this.currentSection = 'confidence';
    }
  }

  /**
   * Answer confidence question
   */
  answerConfidence(rating: number): void {
    this.confidenceQuestions[this.currentConfidenceIndex].userAnswer = rating;
    
    if (this.currentConfidenceIndex < this.confidenceQuestions.length - 1) {
      this.currentConfidenceIndex++;
    } else {
      // Complete test
      this.completeTest();
    }
  }

  /**
   * Complete test and save results
   */
  completeTest(): void {
    this.currentSection = 'complete';
    this.saveResults();
  }

  /**
   * Save test results to backend
   */
  saveResults(): void {
    const results = {
      userName: this.userName,
      timestamp: new Date().toISOString(),
      recognitionAnswers: this.recognitionQuestions.map(q => ({
        questionId: q.id,
        statement: q.statement,
        correctAnswer: q.isTrue,
        userAnswer: q.userAnswer
      })),
      confidenceAnswers: this.confidenceQuestions.map(q => ({
        questionId: q.id,
        question: q.question,
        rating: q.userAnswer
      })),
      recognitionScore: this.calculateRecognitionScore(),
      avgConfidence: this.calculateAverageConfidence()
    };

    // Send to backend
    this.http.post('http://127.0.0.1:8000/api/comprehension-test', results)
      .subscribe({
        next: () => {
          console.log('Comprehension test results saved');
        },
        error: (err) => {
          console.error('Error saving comprehension test:', err);
        }
      });
  }

  /**
   * Calculate recognition score
   */
  calculateRecognitionScore(): number {
    let correct = 0;
    this.recognitionQuestions.forEach(q => {
      if (q.userAnswer === 'unsure') return; // Don't count unsure answers
      
      const userAnsweredTrue = q.userAnswer === 'true';
      if (userAnsweredTrue === q.isTrue) {
        correct++;
      }
    });
    
    const attempted = this.recognitionQuestions.filter(q => q.userAnswer !== 'unsure').length;
    return attempted > 0 ? Math.round((correct / attempted) * 100) : 0;
  }

  /**
   * Calculate average confidence
   */
  calculateAverageConfidence(): number {
    const answers = this.confidenceQuestions
      .map(q => q.userAnswer)
      .filter(a => a !== null) as number[];
    
    if (answers.length === 0) return 0;
    return Math.round((answers.reduce((a, b) => a + b, 0) / answers.length) * 10) / 10;
  }

  /**
   * Continue to thank you page
   */
  continue(): void {
    this.router.navigate(['/thank-you']);
  }

  /**
   * Get current recognition question
   */
  getCurrentRecognitionQuestion(): RecognitionQuestion {
    return this.recognitionQuestions[this.currentRecognitionIndex];
  }

  /**
   * Get current confidence question
   */
  getCurrentConfidenceQuestion(): ConfidenceQuestion {
    return this.confidenceQuestions[this.currentConfidenceIndex];
  }

  /**
   * Get progress for recognition questions
   */
  getRecognitionProgress(): string {
    return `${this.currentRecognitionIndex + 1} / ${this.recognitionQuestions.length}`;
  }

  /**
   * Get progress for confidence questions
   */
  getConfidenceProgress(): string {
    return `${this.currentConfidenceIndex + 1} / ${this.confidenceQuestions.length}`;
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
   * Get confidence label
   */
  getConfidenceLabel(rating: number): string {
    const labels = ['Not at all', 'Slightly', 'Moderately', 'Very', 'Extremely'];
    return labels[rating - 1] || '';
  }
}