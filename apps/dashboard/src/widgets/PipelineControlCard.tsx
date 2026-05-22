import { useState } from "react";
import { startPipeline, stopPipeline } from "../shared/api/pipeline";

type PipelineState = "stopped" | "playing";

export function PipelineControlCard() {
  const [state, setState] = useState<PipelineState>("stopped");
  const [loading, setLoading] = useState(false);

  async function handleToggle() {
    setLoading(true);
    try {
      if (state === "stopped") {
        await startPipeline();
        setState("playing");
      } else {
        await stopPipeline();
        setState("stopped");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="rounded-lg bg-gray-800 p-6">
      <h2 className="text-lg font-semibold text-white mb-4">Pipeline 제어</h2>
      <div className="flex items-center gap-4">
        <span
          className={`px-3 py-1 rounded-full text-sm text-white ${
            state === "playing" ? "bg-green-600" : "bg-gray-600"
          }`}
        >
          {state === "playing" ? "실행 중" : "중지됨"}
        </span>
        <button
          onClick={handleToggle}
          disabled={loading}
          className="px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {loading ? "처리 중..." : state === "playing" ? "중지" : "시작"}
        </button>
      </div>
    </div>
  );
}
