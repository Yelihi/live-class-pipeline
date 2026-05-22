import { useEffect, useRef, useState } from "react";
import type { MetricsSnapshot, SSEEvent } from "../../shared/types/pipeline";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export function usePipelineEvents() {
  const [metrics, setMetrics] = useState<MetricsSnapshot | null>(null);
  const [connected, setConnected] = useState(false);
  const sourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    const source = new EventSource(`${BASE_URL}/events`);
    sourceRef.current = source;

    source.onopen = () => setConnected(true);
    source.onerror = () => setConnected(false);

    source.onmessage = (e: MessageEvent) => {
      const event: SSEEvent = JSON.parse(e.data);
      if (event.type === "metrics") {
        setMetrics(event.data);
      }
    };

    return () => {
      source.close();
      sourceRef.current = null;
      setConnected(false);
    };
  }, []);

  return { metrics, connected, eventSource: sourceRef.current };
}
