"use client";

import { useEffect, useRef, useCallback, useState } from "react";

export interface WSEvent {
  type: string;
  data: Record<string, any>;
  timestamp: string;
}

interface UseAgentWebSocketOptions {
  sessionId: string | null;
  onEvent?: (event: WSEvent) => void;
}

export function useAgentWebSocket({ sessionId, onEvent }: UseAgentWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;

  const connect = useCallback(() => {
    if (!sessionId) return;
    const url = `ws://localhost:8000/ws/agent/${sessionId}`;
    const ws = new WebSocket(url);

    ws.onopen = () => {
      setConnected(true);
    };

    ws.onmessage = (e) => {
      try {
        const event: WSEvent = JSON.parse(e.data);
        onEventRef.current?.(event);
      } catch {
        // ignore non-JSON
      }
    };

    ws.onclose = () => {
      setConnected(false);
    };

    ws.onerror = () => {
      ws.close();
    };

    wsRef.current = ws;
  }, [sessionId]);

  const disconnect = useCallback(() => {
    wsRef.current?.close();
    wsRef.current = null;
    setConnected(false);
  }, []);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return { connected, disconnect };
}
