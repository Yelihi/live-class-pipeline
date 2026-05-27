import type { AggregateBranchMetrics } from "../shared/types/pipeline";

type Branch = "live" | "record" | "ai" | "preview";

const BRANCH_LABELS: Record<Branch, string> = {
  live: "Live 송출",
  record: "녹화",
  ai: "AI 분석",
  preview: "Preview",
};

interface Props {
  branch: Branch;
  metrics?: AggregateBranchMetrics;
}

export function BranchStatusCard({ branch, metrics }: Props) {
  return (
    <div className="rounded-lg bg-gray-800 p-4">
      <h3 className="text-white font-medium">{BRANCH_LABELS[branch]}</h3>
      <div className="mt-2 space-y-1">
        <p className="text-2xl font-bold text-green-400">
          {metrics ? `${metrics.avg_fps.toFixed(1)} fps` : "—"}
        </p>
        <p className="text-gray-400 text-xs">
          총 프레임: {metrics?.total_frames ?? 0}
        </p>
      </div>
    </div>
  );
}
