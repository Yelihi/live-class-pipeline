import {
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { FpsDataPoint } from "../features/metrics-subscribe/useFpsHistory";

interface Props {
  data: FpsDataPoint[];
}

export function FpsChart({ data }: Props) {
  return (
    <div className="rounded-lg bg-gray-800 p-4">
      <h3 className="text-white font-medium mb-3">Branch FPS (최근 60초)</h3>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={data}>
          <XAxis
            dataKey="time"
            tick={{ fill: "#9ca3af", fontSize: 11 }}
            interval="preserveStartEnd"
          />
          <YAxis domain={[0, 35]} tick={{ fill: "#9ca3af", fontSize: 11 }} />
          <Tooltip
            contentStyle={{ backgroundColor: "#1f2937", border: "none" }}
            labelStyle={{ color: "#fff" }}
          />
          <Legend />
          <Line type="monotone" dataKey="live" stroke="#10b981" dot={false} name="Live" />
          <Line type="monotone" dataKey="record" stroke="#3b82f6" dot={false} name="Record" />
          <Line type="monotone" dataKey="ai" stroke="#a855f7" dot={false} name="AI" />
          <Line type="monotone" dataKey="preview" stroke="#f59e0b" dot={false} name="Preview" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
