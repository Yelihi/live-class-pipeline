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

export interface AIResult {
  type: "ai_result";
  pts_ns: number;
  wall_clock_ms: number;
  face_detected: boolean;
  left_ear: number;
  right_ear: number;
  avg_ear: number;
  is_facing_front: boolean;
  attention_score: number;
}

export type SSEEvent = SSEMetricsEvent | SSEPipelineEvent | AIResult;
