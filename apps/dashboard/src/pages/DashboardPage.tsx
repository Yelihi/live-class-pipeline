import { BranchStatusCard } from "../widgets/BranchStatusCard";
import { PipelineControlCard } from "../widgets/PipelineControlCard";

const BRANCHES = ["live", "record", "ai", "preview"] as const;

export function DashboardPage() {
  return (
    <div className="min-h-screen bg-gray-900 p-6">
      <h1 className="text-2xl font-bold text-white mb-6">
        Live Class Pipeline Dashboard
      </h1>
      <div className="space-y-6">
        <PipelineControlCard />
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          {BRANCHES.map((branch) => (
            <BranchStatusCard key={branch} branch={branch} />
          ))}
        </div>
      </div>
    </div>
  );
}
