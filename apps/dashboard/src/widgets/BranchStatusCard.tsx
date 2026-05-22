import type { BranchMetrics } from "../shared/types/pipeline";

type Branch = "live" | "record" | "ai" | "preview";

const BRANCH_LABELS: Record<Branch, string> = {
  live: "Live 송출",
  record: "녹화",
  ai: "AI 분석",
  preview: "Preview",
};

interface Props {
  branch: Branch;
  metrics?: BranchMetrics;
}

export function BranchStatusCard({ branch, metrics }: Props) {
  return (
    <div className="rounded-lg bg-gray-800 p-4">
      <h3 className="text-white font-medium">{BRANCH_LABELS[branch]}</h3>
      <p className="text-gray-400 text-sm mt-1">
        FPS: {metrics ? metrics.fps.toFixed(1) : "—"}
      </p>
      <p className="text-gray-500 text-xs mt-1">
        프레임: {metrics ? metrics.frame_count : "—"}
      </p>
    </div>
  );
}
