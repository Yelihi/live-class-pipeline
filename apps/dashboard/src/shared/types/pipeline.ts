export interface PipelineStatus {
  state: "playing" | "paused" | "stopped" | "null";
}

export interface BranchMetrics {
  fps: number;
  frame_count: number;
  dropped_frames: number;
}

export interface MetricsSnapshot {
  live: BranchMetrics;
  record: BranchMetrics;
  ai: BranchMetrics;
  preview: BranchMetrics;
}

export interface SSEMetricsEvent {
  type: "metrics";
  data: MetricsSnapshot;
  timestamp: number;
}

export interface SSEPipelineEvent {
  type: "pipeline";
  state: "started" | "stopped";
  input?: string;
}

export type SSEEvent = SSEMetricsEvent | SSEPipelineEvent;
