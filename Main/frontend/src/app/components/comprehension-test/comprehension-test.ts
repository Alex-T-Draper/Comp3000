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
  condition: number; // Which reading condition (1–6) this question maps to
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
  
  // Recognition questions split by condition (2–3 per condition)
  // C1=Plain/BazaarBox | C2=Scroll-Gated/VaultDrive | C3=Formatted/ConnectSphere
  // C4=AI Summary/LearnVault | C5=AI Enhanced/PulseFit | C6=AI Hover/SonicWave
  recognitionQuestions: RecognitionQuestion[] = [
    // --- Condition 1: Plain Text — BazaarBox (ecommerce) ---
    {
      id: 1,
      statement: 'BazaarBox charges sellers a transaction fee of 10% on every sale.',
      isTrue: false,
      tosSource: 'ecommerce',
      condition: 1,
      userAnswer: null
    },
    {
      id: 2,
      statement: 'You can get a full refund at any time, even after using the service for months.',
      isTrue: false,
      tosSource: 'ecommerce',
      condition: 1,
      userAnswer: null
    },
    {
      id: 3,
      statement: 'You retain full ownership of content and listings you upload to BazaarBox.',
      isTrue: true,
      tosSource: 'ecommerce',
      condition: 1,
      userAnswer: null
    },
    // --- Condition 2: Scroll-Gated — VaultDrive (cloud storage) ---
    {
      id: 4,
      statement: 'VaultDrive stores your data exclusively in UK and European Economic Area data centres.',
      isTrue: true,
      tosSource: 'cloudstorage',
      condition: 2,
      userAnswer: null
    },
    {
      id: 5,
      statement: 'The company guarantees 100% uptime and will compensate you for any downtime.',
      isTrue: false,
      tosSource: 'cloudstorage',
      condition: 2,
      userAnswer: null
    },
    {
      id: 6,
      statement: 'The service is provided "as is" without warranties.',
      isTrue: true,
      tosSource: 'cloudstorage',
      condition: 2,
      userAnswer: null
    },
    // --- Condition 3: Formatted & Highlighted — ConnectSphere (social media) ---
    {
      id: 7,
      statement: 'The company may share your information with third-party service providers.',
      isTrue: true,
      tosSource: 'socialmedia',
      condition: 3,
      userAnswer: null
    },
    {
      id: 8,
      statement: 'ConnectSphere retains your personal data for up to 3 years after you delete your account.',
      isTrue: true,
      tosSource: 'socialmedia',
      condition: 3,
      userAnswer: null
    },
    {
      id: 9,
      statement: 'ConnectSphere users waive their right to participate in class action lawsuits.',
      isTrue: true,
      tosSource: 'socialmedia',
      condition: 3,
      userAnswer: null
    },
    // --- Condition 4: AI Summary — LearnVault (education) ---
    {
      id: 10,
      statement: 'The company can change the terms at any time without notifying you.',
      isTrue: false,
      tosSource: 'education',
      condition: 4,
      userAnswer: null
    },
    {
      id: 11,
      statement: 'LearnVault certificates are equivalent to formal academic credits.',
      isTrue: false,
      tosSource: 'education',
      condition: 4,
      userAnswer: null
    },
    {
      id: 12,
      statement: 'LearnVault offers a full refund within 14 days if you have completed less than 25% of a course.',
      isTrue: true,
      tosSource: 'education',
      condition: 4,
      userAnswer: null
    },
    // --- Condition 5: AI Enhanced — PulseFit (fitness) ---
    {
      id: 13,
      statement: 'PulseFit may sell your health data to insurance companies.',
      isTrue: false,
      tosSource: 'fitness',
      condition: 5,
      userAnswer: null
    },
    {
      id: 14,
      statement: 'The company is not liable for any indirect or consequential damages.',
      isTrue: true,
      tosSource: 'fitness',
      condition: 5,
      userAnswer: null
    },
    {
      id: 17,
      statement: 'PulseFit permanently deletes your health data within 60 days of account deletion.',
      isTrue: true,
      tosSource: 'fitness',
      condition: 5,
      userAnswer: null
    },
    // --- Condition 6: AI Hover — SonicWave (music streaming) ---
    {
      id: 15,
      statement: 'SonicWave requires you to connect to the internet at least every 30 days to keep offline downloads.',
      isTrue: true,
      tosSource: 'musicstreaming',
      condition: 6,
      userAnswer: null
    },
    {
      id: 16,
      statement: 'Your subscription will automatically renew unless you cancel.',
      isTrue: true,
      tosSource: 'musicstreaming',
      condition: 6,
      userAnswer: null
    },
    {
      id: 18,
      statement: 'SonicWave Free tier subscribers can download music for offline listening.',
      isTrue: false,
      tosSource: 'musicstreaming',
      condition: 6,
      userAnswer: null
    },
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

  // Start the test
  startTest(): void {
    this.currentSection = 'recognition';
  }

  // Answer recognition question
  answerRecognition(answer: 'true' | 'false' | 'unsure'): void {
    this.recognitionQuestions[this.currentRecognitionIndex].userAnswer = answer;
    
    if (this.currentRecognitionIndex < this.recognitionQuestions.length - 1) {
      this.currentRecognitionIndex++;
    } else {
      // Move to confidence questions
      this.currentSection = 'confidence';
    }
  }

  // Answer confidence question
  answerConfidence(rating: number): void {
    this.confidenceQuestions[this.currentConfidenceIndex].userAnswer = rating;
    
    if (this.currentConfidenceIndex < this.confidenceQuestions.length - 1) {
      this.currentConfidenceIndex++;
    } else {
      // Complete test
      this.completeTest();
    }
  }

  // Complete test and save results
  completeTest(): void {
    this.currentSection = 'complete';
    this.saveResults();
  }

  // Save test results to backend
  saveResults(): void {
    const results = {
      userName: this.userName,
      timestamp: new Date().toISOString(),
      recognitionAnswers: this.recognitionQuestions.map(q => ({
        questionId: q.id,
        condition: q.condition,
        tosSource: q.tosSource,
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
      conditionScores: this.getConditionScores(),
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

  // Calculate recognition score
  calculateRecognitionScore(): number {
    const answered = this.recognitionQuestions.filter(q => q.userAnswer !== 'unsure' && q.userAnswer !== null);
    const correct = answered.filter(q => (q.userAnswer === 'true') === q.isTrue).length;
    return answered.length > 0 ? Math.round((correct / answered.length) * 100) : 0;
  }

  // Calculate per-condition recognition scores for dissertation
  getConditionScores(): Array<{ condition: number; label: string; tosName: string; correct: number; total: number; percentage: number }> {
    const conditionMeta: Record<number, { label: string; tosName: string }> = {
      1: { label: 'C1 — Plain Text',          tosName: 'BazaarBox'     },
      2: { label: 'C2 — Scroll-Gated',        tosName: 'VaultDrive'    },
      3: { label: 'C3 — Formatted',           tosName: 'ConnectSphere' },
      4: { label: 'C4 — AI Summary',          tosName: 'LearnVault'    },
      5: { label: 'C5 — AI Enhanced',         tosName: 'PulseFit'      },
      6: { label: 'C6 — AI Hover',            tosName: 'SonicWave'     },
    };

    return [1, 2, 3, 4, 5, 6].map(c => {
      const questions = this.recognitionQuestions.filter(q => q.condition === c);
      const answered   = questions.filter(q => q.userAnswer !== 'unsure' && q.userAnswer !== null);
      const correct    = answered.filter(q => (q.userAnswer === 'true') === q.isTrue).length;
      const total      = questions.length;
      const percentage = answered.length > 0 ? Math.round((correct / answered.length) * 100) : 0;
      return { condition: c, ...conditionMeta[c], correct, total, percentage };
    });
  }

  // Calculate average confidence
  calculateAverageConfidence(): number {
    const answers = this.confidenceQuestions
      .map(q => q.userAnswer)
      .filter(a => a !== null) as number[];
    
    if (answers.length === 0) return 0;
    return Math.round((answers.reduce((a, b) => a + b, 0) / answers.length) * 10) / 10;
  }

  // Continue to thank you page
  continue(): void {
    this.router.navigate(['/thank-you']);
  }

  // Get current recognition question
  getCurrentRecognitionQuestion(): RecognitionQuestion {
    return this.recognitionQuestions[this.currentRecognitionIndex];
  }

  // Get current confidence question
  getCurrentConfidenceQuestion(): ConfidenceQuestion {
    return this.confidenceQuestions[this.currentConfidenceIndex];
  }

  // Get progress for recognition questions
  getRecognitionProgress(): string {
    return `${this.currentRecognitionIndex + 1} / ${this.recognitionQuestions.length}`;
  }

  // Get progress for confidence questions
  getConfidenceProgress(): string {
    return `${this.currentConfidenceIndex + 1} / ${this.confidenceQuestions.length}`;
  }

  // Shuffle array
  private shuffleArray<T>(array: T[]): T[] {
    const shuffled = [...array];
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
  }

  // Get confidence label
  getConfidenceLabel(rating: number): string {
    const labels = ['Not at all', 'Slightly', 'Moderately', 'Very', 'Extremely'];
    return labels[rating - 1] || '';
  }
}