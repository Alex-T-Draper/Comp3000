import { TestBed } from '@angular/core/testing';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { EyeTrackingService } from './eye-tracking';

describe('EyeTrackingService', () => {
  let service: EyeTrackingService;
  let mockWebSocket: any;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(EyeTrackingService);

    // Mock WebSocket
    mockWebSocket = {
      send: vi.fn(),
      close: vi.fn(),
      readyState: WebSocket.OPEN,
      onopen: null,
      onclose: null,
      onerror: null,
      onmessage: null
    };

    // Mock the global WebSocket constructor
    vi.stubGlobal('WebSocket', vi.fn(() => mockWebSocket));
  });

  afterEach(() => {
    service.disconnect();
    vi.clearAllMocks();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('startTracking', () => {
    it('should send start command when WebSocket is open', () => {
      const sessionId = 'test-session-123';
      
      service.startTracking(sessionId);
      
      // Check if send was called
      expect(mockWebSocket.send).toHaveBeenCalledWith(
        JSON.stringify({ action: 'start', sessionId })
      );
    });

    it('should create a new WebSocket connection if not already open', () => {
      const sessionId = 'test-session-456';
      
      service.startTracking(sessionId);
      
      expect(vi.mocked(WebSocket)).toHaveBeenCalledWith('ws://127.0.0.1:8000/ws/eyetracking');
    });

    it('should call send after WebSocket opens', () => {
      const sessionId = 'test-session-789';
      
      service.startTracking(sessionId);
      
      // Simulate WebSocket opening
      if (mockWebSocket.onopen) {
        mockWebSocket.onopen({} as Event);
      }
      
      expect(mockWebSocket.send).toHaveBeenCalled();
    });
  });

  describe('stopTracking', () => {
    it('should send stop command when WebSocket is open', () => {
      const sessionId = 'test-session-stop';
      mockWebSocket.readyState = WebSocket.OPEN;
      
      service.stopTracking(sessionId);
      
      expect(mockWebSocket.send).toHaveBeenCalledWith(
        JSON.stringify({ action: 'stop', sessionId })
      );
    });

    it('should not send command if WebSocket is not open', () => {
      const sessionId = 'test-session-closed';
      mockWebSocket.readyState = WebSocket.CLOSED;
      
      service.stopTracking(sessionId);
      
      expect(mockWebSocket.send).not.toHaveBeenCalled();
    });
  });

  describe('updateScrollPosition', () => {
    it('should send scroll position when WebSocket is open', () => {
      const scrollPosition = 42.5;
      mockWebSocket.readyState = WebSocket.OPEN;
      
      service.updateScrollPosition(scrollPosition);
      
      expect(mockWebSocket.send).toHaveBeenCalledWith(
        JSON.stringify({
          action: 'scroll',
          scrollPosition: scrollPosition
        })
      );
    });

    it('should not send scroll position if WebSocket is not open', () => {
      const scrollPosition = 50;
      mockWebSocket.readyState = WebSocket.CLOSED;
      
      service.updateScrollPosition(scrollPosition);
      
      expect(mockWebSocket.send).not.toHaveBeenCalled();
    });

    it('should handle various scroll positions', () => {
      mockWebSocket.readyState = WebSocket.OPEN;
      const positions = [0, 25, 50, 75, 100];
      
      positions.forEach(pos => {
        service.updateScrollPosition(pos);
      });
      
      expect(mockWebSocket.send).toHaveBeenCalledTimes(positions.length);
    });
  });

  describe('disconnect', () => {
    it('should close the WebSocket connection', () => {
      service.startTracking('test-session');
      
      service.disconnect();
      
      expect(mockWebSocket.close).toHaveBeenCalled();
    });

    it('should handle disconnect when no connection exists', () => {
      // Should not throw error
      expect(() => service.disconnect()).not.toThrow();
    });
  });

  describe('WebSocket error handling', () => {
    it('should handle WebSocket errors gracefully', () => {
      const warnSpy = vi.spyOn(console, 'warn');
      
      service.startTracking('test-session');
      
      if (mockWebSocket.onerror) {
        mockWebSocket.onerror(new Event('error'));
      }
      
      expect(warnSpy).toHaveBeenCalled();
      warnSpy.mockRestore();
    });

    it('should handle WebSocket close event', () => {
      const logSpy = vi.spyOn(console, 'log');
      
      service.startTracking('test-session');
      
      if (mockWebSocket.onclose) {
        mockWebSocket.onclose(new CloseEvent('close'));
      }
      
      expect(logSpy).toHaveBeenCalled();
      logSpy.mockRestore();
    });
  });
});
