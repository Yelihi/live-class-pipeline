import { useEffect, useRef, useState } from "react";
import type { AIResult } from "../../shared/types/pipeline";

const MAX_BUFFER = 100;

function findClosest(results: AIResult[], targetMs: number): AIResult | null {
  const WINDOW_MS = 500;
  const candidates = results.filter(
    (r) => Math.abs(r.wall_clock_ms - targetMs) <= WINDOW_MS
  );
  if (candidates.length === 0) return null;
  return candidates.reduce((a, b) =>
    Math.abs(a.wall_clock_ms - targetMs) < Math.abs(b.wall_clock_ms - targetMs)
      ? a
      : b
  );
}

export function useAIResults(eventSource: EventSource | null) {
  const bufferRef = useRef<AIResult[]>([]);
  const [latestResult, setLatestResult] = useState<AIResult | null>(null);

  useEffect(() => {
    if (!eventSource) return;

    const handler = (e: MessageEvent) => {
      const event = JSON.parse(e.data);
      if (event.type === "ai_result") {
        bufferRef.current = [...bufferRef.current, event as AIResult].slice(-MAX_BUFFER);
        setLatestResult(event as AIResult);
      }
    };

    eventSource.addEventListener("message", handler);
    return () => eventSource.removeEventListener("message", handler);
  }, [eventSource]);

  function getResultAtTime(wallClockMs: number): AIResult | null {
    return findClosest(bufferRef.current, wallClockMs);
  }

  return { latestResult, getResultAtTime };
}
