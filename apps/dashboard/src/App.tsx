import { useState } from "react";
import { DashboardPage } from "./pages/DashboardPage";
import { PublisherPage } from "./pages/PublisherPage";

type Tab = "dashboard" | "publish";

export default function App() {
  const [tab, setTab] = useState<Tab>("dashboard");

  return (
    <>
      <nav className="bg-gray-800 px-6 py-2 flex gap-4">
        <button
          onClick={() => setTab("dashboard")}
          className={`text-sm px-3 py-1 rounded ${
            tab === "dashboard"
              ? "bg-blue-600 text-white"
              : "text-gray-400 hover:text-white"
          }`}
        >
          Dashboard
        </button>
        <button
          onClick={() => setTab("publish")}
          className={`text-sm px-3 py-1 rounded ${
            tab === "publish"
              ? "bg-red-600 text-white"
              : "text-gray-400 hover:text-white"
          }`}
        >
          송출
        </button>
      </nav>
      <div className={tab === "dashboard" ? "" : "hidden"}>
        <DashboardPage />
      </div>
      <div className={tab === "publish" ? "" : "hidden"}>
        <PublisherPage />
      </div>
    </>
  );
}
