// Receive-only WebSocket for the Data UI.
// Where useWebSocket sends control commands out, this only listens for rover data coming in.
import { useEffect, useRef, useState } from "react";
import { type TelemetryState } from "../types/telemetry";

const RECONNECT_DELAY_MS = 3000;

export function useTelemetry(url: string) {
  const [telemetry, setTelemetry] = useState<TelemetryState | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);

  useEffect(() => {
    const connect = () => {
      const ws = new WebSocket(url);
      socketRef.current = ws;

      ws.onopen = () => setIsConnected(true);

      ws.onmessage = (event) => {
        try {
          setTelemetry(JSON.parse(event.data) as TelemetryState);
        } catch {
          // One malformed frame should not tear down the feed.
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        reconnectTimeoutRef.current = window.setTimeout(connect, RECONNECT_DELAY_MS);
      };

      ws.onerror = () => ws.close();
    };

    connect();

    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (socketRef.current) {
        socketRef.current.onclose = null;
        socketRef.current.close();
      }
    };
  }, [url]);

  return { telemetry, isConnected };
}
