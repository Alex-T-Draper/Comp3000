// src/app/components/thank-you/thank-you.ts
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';

@Component({
  selector: 'app-thank-you',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './thank-you.html',
  styleUrls: ['./thank-you.scss']
})
export class ThankYouComponent implements OnInit {
  formUrl: SafeResourceUrl;
  userName: string = '';

  constructor(private sanitizer: DomSanitizer) {
    // Sanitize the Google Form URL for embedding
    this.formUrl = this.sanitizer.bypassSecurityTrustResourceUrl(
      'https://docs.google.com/forms/d/e/1FAIpQLSeZCH8TNp7pI-A_WTnf1_AwaozqhDg2ajaKzcsugBL6DKnCaw/viewform?embedded=true'
    );
  }

  ngOnInit(): void {
    // Get user name from session storage
    this.userName = sessionStorage.getItem('userName') || 'Participant';
  }

  /**
   * Open form in new tab
   */
  openFormInNewTab(): void {
    window.open(
      'https://docs.google.com/forms/d/e/1FAIpQLSeZCH8TNp7pI-A_WTnf1_AwaozqhDg2ajaKzcsugBL6DKnCaw/viewform?usp=header',
      '_blank'
    );
  }
}