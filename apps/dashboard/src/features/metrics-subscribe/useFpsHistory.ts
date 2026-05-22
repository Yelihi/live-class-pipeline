import { useEffect, useState } from "react";
import type { MetricsSnapshot } from "../../shared/types/pipeline";

export interface FpsDataPoint {
  time: string;
  live: number;
  record: number;
  ai: number;
  preview: number;
}

const MAX_POINTS = 60;

export function useFpsHistory(metrics: MetricsSnapshot | null) {
  const [history, setHistory] = useState<FpsDataPoint[]>([]);

  useEffect(() => {
    if (!metrics) return;
    const point: FpsDataPoint = {
      time: new Date().toLocaleTimeString(),
      live: metrics.live.fps,
      record: metrics.record.fps,
      ai: metrics.ai.fps,
      preview: metrics.preview.fps,
    };
    setHistory((prev) => [...prev, point].slice(-MAX_POINTS));
  }, [metrics]);

  return history;
}
