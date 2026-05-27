import { useAIResults } from "../features/metrics-subscribe/useAIResults";
import { useFpsHistory } from "../features/metrics-subscribe/useFpsHistory";
import { usePipelineEvents } from "../features/metrics-subscribe/usePipelineEvents";
import { AIResultPanel } from "../widgets/AIResultPanel";
import { BranchStatusCard } from "../widgets/BranchStatusCard";
import { FpsChart } from "../widgets/FpsChart";
import { PipelineControlCard } from "../widgets/PipelineControlCard";
import { WhepPlayer } from "../widgets/WhepPlayer";

const BRANCHES = ["live", "record", "ai", "preview"] as const;
const WHEP_URL = `${import.meta.env.VITE_MEDIAMTX_URL ?? "http://localhost:8889"}/room1/whep`;

export function DashboardPage() {
  const { metrics, connected, eventSource } = usePipelineEvents();
  const fpsHistory = useFpsHistory(metrics);
  const { latestResult } = useAIResults(eventSource);

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
              metrics={metrics?.aggregate?.[branch]}
            />
          ))}
        </div>

        <FpsChart data={fpsHistory} />

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <WhepPlayer src={WHEP_URL} />
          <AIResultPanel result={latestResult} />
        </div>
      </div>
    </div>
  );
}
