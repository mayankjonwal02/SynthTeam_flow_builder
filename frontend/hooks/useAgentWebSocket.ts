"use client";

import { useEffect, useRef, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { WS_URL } from "@/lib/api";

export interface WSEvent {
  type: string;
  data: Record<string, any>;
  timestamp: string;
}

interface UseAgentWebSocketOptions {
  sessionId: string | null;
  onEvent?: (event: WSEvent) => void;
}

const MAX_RETRY_DELAY_MS = 15000;
// Closed by the server for auth/ownership reasons: retrying won't help
const POLICY_VIOLATION = 1008;

export function useAgentWebSocket({ sessionId, onEvent }: UseAgentWebSocketOptions) {
  const { getToken } = useAuth();
  const [connected, setConnected] = useState(false);
  const onEventRef = useRef(onEvent);
  const getTokenRef = useRef(getToken);

  useEffect(() => {
    onEventRef.current = onEvent;
    getTokenRef.current = getToken;
  });

  useEffect(() => {
    if (!sessionId) return;

    let ws: WebSocket | null = null;
    let stopped = false;
    let retryTimer: ReturnType<typeof setTimeout> | undefined;
    let attempt = 0;

    const connect = async () => {
      // Browsers can't send headers on WebSockets, so the token goes in the query string
      const token = await getTokenRef.current();
      if (stopped) return;
      const url = `${WS_URL}/ws/agent/${sessionId}?token=${encodeURIComponent(token ?? "")}`;
      ws = new WebSocket(url);

      ws.onopen = () => {
        attempt = 0;
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

      ws.onclose = (e) => {
        setConnected(false);
        if (stopped || e.code === POLICY_VIOLATION) return;
        // Reconnect with exponential backoff (fresh token each time)
        const delay = Math.min(1000 * 2 ** attempt, MAX_RETRY_DELAY_MS);
        attempt += 1;
        retryTimer = setTimeout(connect, delay);
      };

      ws.onerror = () => {
        ws?.close();
      };
    };

    connect();

    return () => {
      stopped = true;
      clearTimeout(retryTimer);
      ws?.close();
      setConnected(false);
    };
  }, [sessionId]);

  return { connected };
}
