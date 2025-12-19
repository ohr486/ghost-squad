"use client";

import { useState } from "react";
import { LivingKanban } from "../components/LivingKanban";

export default function Home() {
  const [instruction, setInstruction] = useState("");
  const [missionData, setMissionData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const startMission = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/mission/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ instruction }),
      });
      const data = await res.json();
      setMissionData(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-50 p-8 text-slate-800">
      {/* Header */}
      <header className="flex justify-between items-center mb-12">
        <h1 className="text-2xl font-bold tracking-tighter">
          PROJECT: <span className="text-blue-600">GHOST-SQUAD</span>
        </h1>
        <div className="text-xs font-mono text-slate-400">
          SYNC RATE: <span className="text-blue-500">100%</span>
        </div>
      </header>

      {/* Control Center */}
      <div className="max-w-2xl mx-auto mb-12 flex gap-2">
        <input
          type="text"
          value={instruction}
          onChange={(e) => setInstruction(e.target.value)}
          placeholder="司令官、指示を入力してください..."
          className="flex-1 p-3 border border-slate-200 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          onClick={startMission}
          disabled={loading}
          className="bg-blue-600 text-white px-6 py-3 rounded-lg font-bold hover:bg-blue-700 disabled:opacity-50 transition-all"
        >
          {loading ? "DEPLOYING..." : "MISSION START"}
        </button>
      </div>

      {/* Mission Result */}
      {missionData && (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          
          {/* Logs Panel (左側 1カラム) */}
          <div className="lg:col-span-1 bg-black text-green-400 p-6 rounded-xl font-mono text-sm h-[500px] overflow-y-auto shadow-2xl border border-slate-800">
            <h3 className="text-slate-500 mb-4 border-b border-slate-800 pb-2 text-xs uppercase">Ghost_Logs</h3>
            <ul className="space-y-3">
              {missionData.logs.map((log: string, i: number) => (
                <li key={i} className="flex gap-3 text-xs leading-relaxed opacity-80 hover:opacity-100 transition-opacity">
                  <span className="text-slate-600">[{i.toString().padStart(2, '0')}]</span>
                  <span>{log}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Living Kanban (右側 3カラム) */}
          <div className="lg:col-span-3">
            <LivingKanban initialTasks={missionData.tasks} />
          </div>
          
        </div>
      )}
    </main>
  );
}

