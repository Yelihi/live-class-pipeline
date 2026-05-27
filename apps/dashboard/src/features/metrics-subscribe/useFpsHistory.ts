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
    if (!metrics?.aggregate) return;
    const agg = metrics.aggregate;
    const point: FpsDataPoint = {
      time: new Date().toLocaleTimeString(),
      live: agg.live?.avg_fps ?? 0,
      record: agg.record?.avg_fps ?? 0,
      ai: agg.ai?.avg_fps ?? 0,
      preview: agg.preview?.avg_fps ?? 0,
    };
    setHistory((prev) => [...prev, point].slice(-MAX_POINTS));
  }, [metrics]);

  return history;
}
