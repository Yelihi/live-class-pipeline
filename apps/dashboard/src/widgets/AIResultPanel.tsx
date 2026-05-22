import type { AIResult } from "../shared/types/pipeline";

interface Props {
  result: AIResult | null;
}

export function AIResultPanel({ result }: Props) {
  if (!result) {
    return (
      <div className="rounded-lg bg-gray-800 p-4">
        <h3 className="text-white font-medium">AI 집중도 분석</h3>
        <p className="text-gray-500 mt-2 text-sm">대기 중...</p>
      </div>
    );
  }

  const attentionPct = Math.round(result.attention_score * 100);
  const color =
    attentionPct >= 70
      ? "text-green-400"
      : attentionPct >= 40
        ? "text-yellow-400"
        : "text-red-400";
  const barColor =
    attentionPct >= 70
      ? "bg-green-500"
      : attentionPct >= 40
        ? "bg-yellow-500"
        : "bg-red-500";

  return (
    <div className="rounded-lg bg-gray-800 p-4 space-y-3">
      <h3 className="text-white font-medium">AI 집중도 분석</h3>

      {!result.face_detected ? (
        <p className="text-gray-500 text-sm">얼굴 미감지</p>
      ) : (
        <>
          <div>
            <div className="flex justify-between mb-1">
              <span className="text-gray-400 text-sm">집중도</span>
              <span className={`font-bold ${color}`}>{attentionPct}%</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all ${barColor}`}
                style={{ width: `${attentionPct}%` }}
              />
            </div>
          </div>

          <div className="flex gap-6 text-sm">
            <span className="text-gray-400">
              왼쪽 눈{" "}
              <span className="text-white">{result.left_ear.toFixed(3)}</span>
            </span>
            <span className="text-gray-400">
              오른쪽 눈{" "}
              <span className="text-white">{result.right_ear.toFixed(3)}</span>
            </span>
            <span className="text-gray-400">
              정면{" "}
              <span className={result.is_facing_front ? "text-green-400" : "text-red-400"}>
                {result.is_facing_front ? "✓" : "✗"}
              </span>
            </span>
          </div>
        </>
      )}

      <p className="text-gray-600 text-xs">
        분석 시각: {new Date(result.wall_clock_ms).toLocaleTimeString()}
      </p>
    </div>
  );
}
