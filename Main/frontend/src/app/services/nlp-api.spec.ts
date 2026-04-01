import { TestBed } from '@angular/core/testing';
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { NlpApiService, NLPAnalysisResponse } from './nlp-api';

describe('NlpApiService', () => {
  let service: NlpApiService;
  let httpTestingController: HttpTestingController;
  const apiUrl = 'http://127.0.0.1:8000';

  beforeEach(() => {
    TestBed.resetTestingModule();
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [NlpApiService]
    });

    service = TestBed.inject(NlpApiService);
    httpTestingController = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTestingController.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('analyzeTos', () => {
    it('should send POST request with correct parameters', () => {
      const testText = 'Terms of Service text here';
      const numSentences = 5;
      const abstractive = false;

      service.analyzeTos(testText, numSentences, abstractive).subscribe();

      const req = httpTestingController.expectOne(`${apiUrl}/api/summarize`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual({
        text: testText,
        num_sentences: numSentences,
        abstractive: abstractive
      });
    });

    it('should use default values when not provided', () => {
      const testText = 'Some ToS text';

      service.analyzeTos(testText).subscribe();

      const req = httpTestingController.expectOne(`${apiUrl}/api/summarize`);
      expect(req.request.body.num_sentences).toBe(6);
      expect(req.request.body.abstractive).toBe(false);
    });

    it('should handle NLP analysis response correctly', () => {
      const testText = 'Test ToS content';
      const mockResponse: NLPAnalysisResponse = {
        bullets: ['Point 1', 'Point 2'],
        keywords: ['keyword1', 'keyword2'],
        detected_clauses: {},
        grouped_clauses: {},
        risk: {
          per_category: {},
          raw_total: 45,
          normalized_percent: 45
        },
        affects_user: [],
        abstractive: 'Summary text'
      };

      service.analyzeTos(testText).subscribe(result => {
        expect(result.bullets).toEqual(['Point 1', 'Point 2']);
        expect(result.keywords).toEqual(['keyword1', 'keyword2']);
        expect(result.risk.normalized_percent).toBe(45);
        expect(result.abstractive).toBe('Summary text');
      });

      const req = httpTestingController.expectOne(`${apiUrl}/api/summarize`);
      req.flush(mockResponse);
    });

    it('should handle abstractive summarization', () => {
      const testText = 'Long ToS text';
      const abstractive = true;

      service.analyzeTos(testText, 6, abstractive).subscribe();

      const req = httpTestingController.expectOne(`${apiUrl}/api/summarize`);
      expect(req.request.body.abstractive).toBe(true);
    });

    it('should handle various sentence counts', () => {
      const testText = 'Test text';
      const sentenceCounts = [3, 5, 8, 10];

      sentenceCounts.forEach(count => {
        service.analyzeTos(testText, count).subscribe();
        const req = httpTestingController.expectOne(`${apiUrl}/api/summarize`);
        expect(req.request.body.num_sentences).toBe(count);
      });
    });

    it('should handle HTTP errors gracefully', () => {
      const testText = 'Test ToS';
      let errorReceived = false;

      service.analyzeTos(testText).subscribe(
        () => {
          throw new Error('Expected request to fail');
        },
        (error) => {
          errorReceived = true;
          expect(error.status).toBe(500);
        }
      );

      const req = httpTestingController.expectOne(`${apiUrl}/api/summarize`);
      req.flush('Internal Server Error', { status: 500, statusText: 'Internal Server Error' });
      expect(errorReceived).toBe(true);
    });
  });

  describe('loadTosFile', () => {
    it('should request ToS file from correct endpoint', () => {
      const filename = 'ecommerce_tos';

      service.loadTosFile(filename).subscribe();

      const req = httpTestingController.expectOne(`${apiUrl}/api/tos/${filename}`);
      expect(req.request.method).toBe('GET');
      expect(req.request.responseType).toBe('text');
    });

    it('should return text content', () => {
      const filename = 'privacy_policy';
      const mockContent = 'This is the privacy policy content...';

      service.loadTosFile(filename).subscribe(content => {
        expect(content).toBe(mockContent);
      });

      const req = httpTestingController.expectOne(`${apiUrl}/api/tos/${filename}`);
      req.flush(mockContent);
    });

    it('should handle file not found errors', () => {
      const filename = 'nonexistent_file';
      let errorReceived = false;

      service.loadTosFile(filename).subscribe(
        () => {
          throw new Error('Expected request to fail');
        },
        (error) => {
          errorReceived = true;
          expect(error.status).toBe(404);
        }
      );

      const req = httpTestingController.expectOne(`${apiUrl}/api/tos/${filename}`);
      req.flush('Not Found', { status: 404, statusText: 'Not Found' });
      expect(errorReceived).toBe(true);
    });

    it('should handle various file types', () => {
      const filenames = [
        'ecommerce_tos',
        'fitness_tos',
        'musicstreaming_tos',
        'socialmedia_tos',
        'education_tos',
        'cloudstorage_tos'
      ];

      filenames.forEach(filename => {
        service.loadTosFile(filename).subscribe(content => {
          expect(content).toBeTruthy();
        });

        const req = httpTestingController.expectOne(`${apiUrl}/api/tos/${filename}`);
        req.flush(`Content for ${filename}`);
      });
    });

    it('should handle network errors', () => {
      const filename = 'test_tos';
      let errorReceived = false;

      service.loadTosFile(filename).subscribe(
        () => {
          throw new Error('Expected request to fail');
        },
        (error) => {
          errorReceived = true;
        }
      );

      const req = httpTestingController.expectOne(`${apiUrl}/api/tos/${filename}`);
      req.error(new ErrorEvent('Network error'));
      expect(errorReceived).toBe(true);
    });
  });

  describe('concurrent requests', () => {
    it('should handle multiple simultaneous requests', () => {
      const text1 = 'First ToS';
      const text2 = 'Second ToS';

      service.analyzeTos(text1).subscribe();
      service.analyzeTos(text2).subscribe();

      const requests = httpTestingController.match(`${apiUrl}/api/summarize`);
      expect(requests.length).toBe(2);
      
      requests[0].flush({ bullets: ['point1'], keywords: [], detected_clauses: {}, grouped_clauses: {}, risk: { per_category: {}, raw_total: 0, normalized_percent: 0 }, affects_user: [], abstractive: 'sum1' });
      requests[1].flush({ bullets: ['point2'], keywords: [], detected_clauses: {}, grouped_clauses: {}, risk: { per_category: {}, raw_total: 0, normalized_percent: 0 }, affects_user: [], abstractive: 'sum2' });
    });
  });
});
