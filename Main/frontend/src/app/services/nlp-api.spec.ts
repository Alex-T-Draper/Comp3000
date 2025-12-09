import { TestBed } from '@angular/core/testing';

import { NlpApi } from './nlp-api';

describe('NlpApi', () => {
  let service: NlpApi;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(NlpApi);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
