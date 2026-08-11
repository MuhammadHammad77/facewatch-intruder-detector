import { useEffect, useRef } from 'react';
import { useStore } from '../store/useStore';
import type { Alert } from '../store/useStore';
import { toast } from 'sonner';
import { playAlertSound } from '../utils/audio';

export const useAlertWebSocket = () => {
  const { setWsStatus, addLiveAlert, incrementUnreviewed } = useStore();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    let attempts = 0;
    const maxAttempts = 5;

    const connect = () => {
      if (wsRef.current?.readyState === WebSocket.OPEN) return;
      
      const wsUrl = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace('http', 'ws') + '/api/alerts/ws';
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setWsStatus('connected');
        attempts = 0;
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'unknown_detected' && data.alert) {
            const alert: Alert = data.alert;
            addLiveAlert(alert);
            incrementUnreviewed();
            toast.error(`🚨 Unknown Person Detected on ${alert.camera_source}`);
            
            // Beep sound
            playAlertSound('beep');
          }
        } catch (e) {
          console.error("Failed to parse websocket message", e);
        }
      };

      ws.onclose = () => {
        if (attempts >= maxAttempts) {
          setWsStatus('disconnected');
          toast.error("WebSocket connection lost");
        } else {
          setWsStatus('reconnecting');
          attempts++;
          reconnectTimeoutRef.current = setTimeout(connect, 3000);
        }
      };
      
      ws.onerror = () => {
         ws.close();
      };
    };

    connect();

    // Ping every 30s
    const pingInterval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);

    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      clearInterval(pingInterval);
      if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) {
         wsRef.current.close();
      }
    };
  }, [setWsStatus, addLiveAlert, incrementUnreviewed]);
};
