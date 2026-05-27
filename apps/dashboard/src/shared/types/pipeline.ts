export interface PipelineStatus {
  state: "playing" | "paused" | "stopped" | "null";
  room_count?: number;
}

export interface BranchMetrics {
  fps: number;
  frame_count: number;
}

export interface AggregateBranchMetrics {
  avg_fps: number;
  total_frames: number;
}

export interface MetricsSnapshot {
  rooms: Record<string, Record<string, BranchMetrics>>;
  aggregate: Record<string, AggregateBranchMetrics>;
}

export interface SSEMetricsEvent {
  type: "metrics";
  data: MetricsSnapshot;
  timestamp: number;
}

export interface SSEPipelineEvent {
  type: "pipeline";
  state: "started" | "stopped";
  rooms?: string[];
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
