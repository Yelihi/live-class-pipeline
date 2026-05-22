import type { MetricsSnapshot, PipelineStatus } from "../types/pipeline";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export async function startPipeline(inputPath?: string): Promise<{ state: string }> {
  const url = inputPath
    ? `${BASE_URL}/pipeline/start?input_path=${encodeURIComponent(inputPath)}`
    : `${BASE_URL}/pipeline/start`;
  const res = await fetch(url, { method: "POST" });
  return res.json();
}

export async function stopPipeline(): Promise<{ state: string }> {
  const res = await fetch(`${BASE_URL}/pipeline/stop`, { method: "POST" });
  return res.json();
}

export async function getPipelineStatus(): Promise<PipelineStatus> {
  const res = await fetch(`${BASE_URL}/pipeline/status`);
  return res.json();
}

export async function getMetrics(): Promise<MetricsSnapshot> {
  const res = await fetch(`${BASE_URL}/metrics`);
  return res.json();
}

export function createEventSource(): EventSource {
  return new EventSource(`${BASE_URL}/events`);
}
