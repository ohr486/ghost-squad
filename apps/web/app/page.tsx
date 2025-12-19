"use client";

import { useState } from "react";

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

      {/* Mission Result (Simple Kanban View) */}
      {missionData && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          
          {/* Logs Panel */}
          <div className="bg-black text-green-400 p-6 rounded-xl font-mono text-sm h-96 overflow-y-auto shadow-2xl">
            <h3 className="text-slate-500 mb-4 border-b border-slate-800 pb-2">GHOST_LOGS</h3>
            <ul className="space-y-2">
              {missionData.logs.map((log: string, i: number) => (
                <li key={i} className="animate-pulse">
                  <span className="opacity-50 mr-2">[{i.toString().padStart(2, '0')}]</span>
                  {log}
                </li>
              ))}
            </ul>
          </div>

          {/* Task List (Proto-Kanban) */}
          <div className="space-y-4">
            <h3 className="font-bold text-slate-400 text-sm uppercase">Generated Tasks</h3>
            {missionData.tasks.map((task: any) => (
              <div key={task.id} className="bg-white p-4 rounded-lg shadow-sm border-l-4 border-blue-500 flex justify-between items-center">
                <div>
                  <h4 className="font-bold text-slate-700">{task.title}</h4>
                  <p className="text-xs text-slate-400 mt-1">Assignee: {task.assignee || "UNASSIGNED"}</p>
                </div>
                <div className="text-right">
                  <span className={`text-xs font-bold px-2 py-1 rounded ${
                    task.status === 'done' ? 'bg-green-100 text-green-600' :
                    task.status === 'working' ? 'bg-blue-100 text-blue-600' : 'bg-slate-100 text-slate-500'
                  }`}>
                    {task.status.toUpperCase()}
                  </span>
                  <div className="text-[10px] text-slate-400 mt-1">${task.energy}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </main>
  );
}

