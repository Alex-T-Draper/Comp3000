// src/app/services/nlp-api.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface ClauseContext {
  before: string;
  sentence: string;
  after: string;
  full_context: string;
  position: {
    start: number;
    end: number;
  };
}

export interface ClauseDetection {
  sentence: string;
  context: ClauseContext;
  matched_keywords: string[];
}

export interface CategoryMetadata {
  title: string;
  user_summary: string;
  explanation: string;
}

export interface GroupedCategory {
  metadata: CategoryMetadata;
  detections: ClauseDetection[];
}

export interface ClauseGroup {
  description: string;
  severity: 'high' | 'medium' | 'low';
  icon: string;
  total_mentions: number;
  categories: { [key: string]: GroupedCategory };
}

export interface RiskScore {
  per_category: { [key: string]: { mentions: number; score: number; weight: number } };
  raw_total: number;
  normalized_percent: number;
}

export interface NLPAnalysisResponse {
  bullets: string[];
  keywords: string[];
  detected_clauses: { [key: string]: ClauseDetection[] };
  grouped_clauses: { [key: string]: ClauseGroup };
  risk: RiskScore;
  affects_user: Array<{
    category: string;
    title: string;
    summary: string;
    explanation: string;
    mentions: number;
  }>;
  abstractive: string;
}

export interface SummarizeRequest {
  text: string;
  num_sentences?: number;
  abstractive?: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class NlpApiService {
  private apiUrl = 'http://127.0.0.1:8000'; // FastAPI backend

  constructor(private http: HttpClient) { }

  /**
   * Generate summary and analysis of ToS text
   */
  analyzeTos(text: string, numSentences: number = 6, abstractive: boolean = false): Observable<NLPAnalysisResponse> {
    const request: SummarizeRequest = {
      text,
      num_sentences: numSentences,
      abstractive
    };

    return this.http.post<NLPAnalysisResponse>(`${this.apiUrl}/summarize`, request);
  }
}