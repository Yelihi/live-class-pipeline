import { usePipelineEvents } from "../features/metrics-subscribe/usePipelineEvents";
import { useFpsHistory } from "../features/metrics-subscribe/useFpsHistory";
import { BranchStatusCard } from "../widgets/BranchStatusCard";
import { FpsChart } from "../widgets/FpsChart";
import { HlsPlayer } from "../widgets/HlsPlayer";
import { PipelineControlCard } from "../widgets/PipelineControlCard";

const HLS_URL = `${import.meta.env.VITE_API_URL ?? "http://localhost:8000"}/hls/stream.m3u8`;

const BRANCHES = ["live", "record", "ai", "preview"] as const;

export function DashboardPage() {
  const { metrics, connected } = usePipelineEvents();
  const fpsHistory = useFpsHistory(metrics);

  return (
    <div className="min-h-screen bg-gray-900 p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">
          Live Class Pipeline Dashboard
        </h1>
        <span
          className={`px-2 py-1 rounded-full text-xs ${
            connected
              ? "bg-green-900 text-green-300"
              : "bg-gray-700 text-gray-400"
          }`}
        >
          {connected ? "● SSE 연결됨" : "○ 연결 끊김"}
        </span>
      </div>
      <div className="space-y-6">
        <PipelineControlCard />
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          {BRANCHES.map((branch) => (
            <BranchStatusCard
              key={branch}
              branch={branch}
              metrics={metrics?.[branch]}
            />
          ))}
        </div>
        <FpsChart data={fpsHistory} />
        <HlsPlayer src={HLS_URL} />
      </div>
    </div>
  );
}
