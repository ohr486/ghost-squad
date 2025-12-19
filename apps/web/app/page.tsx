"use client";

import { useState } from "react";
import { LivingKanban } from "../components/LivingKanban";

// 初期の空データ定義
const INITIAL_LOGS = [
  "SYSTEM BOOT SEQUENCE INITIATED...",
  "CONNECTING TO GHOST-CORE...",
  "ESTABLISHED SECURE CONNECTION.",
  "WAITING FOR COMMANDER'S ORDER."
];

const INITIAL_TASKS: any[] = [];

export default function Home() {
  const [instruction, setInstruction] = useState("");
  // missionDataをnullではなく、初期オブジェクトで開始する
  const [missionData, setMissionData] = useState({
    logs: INITIAL_LOGS,
    tasks: INITIAL_TASKS
  });
  const [loading, setLoading] = useState(false);

  const startMission = async () => {
    setLoading(true);
    // ログに「通信中...」を追加する演出
    setMissionData(prev => ({
      ...prev,
      logs: [...prev.logs, ">>> TRANSMITTING ORDERS TO SQUAD..."]
    }));

    try {
      const res = await fetch("http://localhost:8000/mission/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ instruction }),
      });
      const data = await res.json();
      
      // 既存のログに新しいログを追記する形で結合
      setMissionData(prev => ({
        logs: [...prev.logs, ...data.logs],
        tasks: data.tasks 
      }));
      
    } catch (e) {
      console.error(e);
      setMissionData(prev => ({
        ...prev,
        logs: [...prev.logs, "!!! CONNECTION ERROR: GHOST-CORE NOT RESPONDING"]
      }));
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-50 p-8 text-slate-800 flex flex-col">
      {/* Header */}
      <header className="flex justify-between items-center mb-8">
        <h1 className="text-2xl font-bold tracking-tighter">
          PROJECT: <span className="text-blue-600">GHOST-SQUAD</span>
        </h1>
        <div className="flex items-center gap-4">
            <div className="text-xs font-mono text-slate-400">
            STATUS: <span className="text-green-500 animate-pulse">ONLINE</span>
            </div>
            <div className="text-xs font-mono text-slate-400">
            SYNC: <span className="text-blue-500">100%</span>
            </div>
        </div>
      </header>

      {/* Control Center */}
      <div className="max-w-3xl mx-auto mb-8 w-full flex gap-2">
        <input
          type="text"
          value={instruction}
          onChange={(e) => setInstruction(e.target.value)}
          placeholder="司令官、指示を入力してください..."
          className="flex-1 p-3 border border-slate-200 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
          onKeyDown={(e) => e.key === 'Enter' && startMission()}
        />
        <button
          onClick={startMission}
          disabled={loading}
          className="bg-blue-600 text-white px-6 py-3 rounded-lg font-bold hover:bg-blue-700 disabled:opacity-50 transition-all text-sm tracking-wider"
        >
          {loading ? "DEPLOYING..." : "EXECUTE"}
        </button>
      </div>

      {/* Mission Result (Always Visible) */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 flex-1">
          
        {/* Logs Panel (左側 1カラム) */}
        <div className="lg:col-span-1 bg-black text-green-400 p-4 rounded-xl font-mono text-xs overflow-y-auto shadow-xl border border-slate-800 flex flex-col h-[600px] lg:h-auto">
          <div className="flex justify-between items-center mb-2 border-b border-slate-800 pb-2">
            <h3 className="text-slate-500 uppercase">Ghost_Logs</h3>
            <div className="w-2 h-2 bg-green-500 rounded-full animate-ping"></div>
          </div>
          <ul className="space-y-2 flex-1 overflow-y-auto pr-2 custom-scrollbar">
            {missionData.logs.map((log: string, i: number) => (
              <li key={i} className="flex gap-2 leading-relaxed opacity-90">
                <span className="text-slate-600 select-none">[{i.toString().padStart(2, '0')}]</span>
                <span>{log}</span>
              </li>
            ))}
            {loading && (
               <li className="flex gap-2 leading-relaxed text-blue-400 animate-pulse">
                <span className="text-slate-600">...</span>
                <span>Thinking...</span>
              </li>
            )}
          </ul>
        </div>

        {/* Living Kanban (右側 3カラム) */}
        <div className="lg:col-span-3 h-[600px] lg:h-auto">
          {/* ここで常にコンポーネントを表示 */}
          <LivingKanban initialTasks={missionData.tasks} />
        </div>
        
      </div>
    </main>
  );
}
