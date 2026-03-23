// src/app/services/eye-tracking.ts
import { Injectable, OnDestroy } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class EyeTrackingService implements OnDestroy {
  private ws: WebSocket | null = null;
  private readonly wsUrl = 'ws://127.0.0.1:8000/ws/eyetracking';
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 3;

  /**
   * Start eye tracking for a session.
   * Connects the WebSocket if not already open, then sends the start command.
   */
  startTracking(sessionId: string): void {
    const send = () => {
      this.ws!.send(JSON.stringify({ action: 'start', sessionId }));
      console.log('[EyeTracking] Start command sent for session:', sessionId);
    };

    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      send();
      return;
    }

    // Connect and send start once open
    this.ws = new WebSocket(this.wsUrl);

    this.ws.onopen = () => {
      console.log('[EyeTracking] WebSocket connected');
      this.reconnectAttempts = 0;
      send();
    };

    this.ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      console.log('[EyeTracking] Response:', msg);
    };

    this.ws.onerror = (error) => {
      console.warn('[EyeTracking] WebSocket error (eye tracker may not be running):', error);
    };

    this.ws.onclose = () => {
      console.log('[EyeTracking] WebSocket closed');
    };
  }

  /**
   * Stop eye tracking for a session.
   * The backend will save the gaze data to the database.
   */
  stopTracking(sessionId: string): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ action: 'stop', sessionId }));
      console.log('[EyeTracking] Stop command sent for session:', sessionId);
    }
  }

  /**
   * Disconnect the WebSocket.
   */
  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  ngOnDestroy(): void {
    this.disconnect();
  }
}
