"use client";

import { useState, useEffect } from "react";
import { LivingKanban } from "../components/LivingKanban";

const INITIAL_LOGS = [
  "SYSTEM BOOT SEQUENCE INITIATED...",
  "CONNECTING TO GHOST-CORE...",
  "ESTABLISHED SECURE CONNECTION.",
  "WAITING FOR COMMANDER'S ORDER."
];

export default function Home() {
  const [instruction, setInstruction] = useState("");
  const [missionData, setMissionData] = useState<any>({
    mission_id: null,
    logs: INITIAL_LOGS,
    tasks: []
  });
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  // --- 監視システム (Polling Hook) ---
  useEffect(() => {
    const syncMissions = async () => {
      try {
        const res = await fetch("http://localhost:8000/missions");
        if (res.ok) {
          const historyData = await res.json();
          setHistory(historyData);

          if (historyData.length > 0) {
            setMissionData((prev: any) => {
              // id か mission_id のどちらかがあれば「選択中」とみなす
              const currentId = prev.id || prev.mission_id;

              // 1. まだ何も選択していない場合のみ、最新(historyData[0])を表示
              if (!currentId) {
                return historyData[0];
              }

	      // 2. 現在見ているミッションと同じIDのものを、新しい履歴リストから探す
              const currentInHistory = historyData.find((m: any) => m.id === currentId);

	      if (currentInHistory) {
                 // 変更がある場合だけ更新（再レンダリング防止）
                 // JSON.stringifyで比較するのが一番確実かつ簡単です
                 if (JSON.stringify(prev.logs) !== JSON.stringify(currentInHistory.logs) || 
                     JSON.stringify(prev.tasks) !== JSON.stringify(currentInHistory.tasks) ||
                     prev.status !== currentInHistory.status) {
                    return currentInHistory;
                 }
              }

	      // 見ているミッションが履歴になければ（あり得ないですが）、そのまま維持
              return prev;
            });
          }
        }
      } catch (e) {
        console.error("Sync Error:", e);
      }
    };

    syncMissions();
    const interval = setInterval(syncMissions, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleSelectMission = (mission: any) => {
    setMissionData(mission);
  };

  const startMission = async () => {
    if (!instruction.trim()) return;
    setLoading(true);
    setMissionData({
      mission_id: "pending...",
      logs: ["Start Mission...", `>>> ${instruction}`],
      tasks: []
    });

    try {
      const res = await fetch("http://localhost:8000/mission/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ instruction }),
      });
      const newMission = await res.json();
      setMissionData(newMission);
      setInstruction(""); 
    } catch (e) {
      console.error(e);
      setMissionData((prev: any) => ({
        ...prev,
        logs: [...prev.logs, "!!! CONNECTION ERROR"]
      }));
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="h-screen w-full bg-slate-50 text-slate-800 flex flex-col overflow-hidden font-sans">
      {/* Header */}
      <div className="p-6 pb-0 flex-none">
        <header className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold tracking-tighter">
            PROJECT: <span className="text-blue-600">GHOST-SQUAD</span>
          </h1>
          <div className="flex items-center gap-4">
              <div className="text-xs font-mono text-slate-400">
              STATUS: <span className="text-green-500 animate-pulse">ONLINE</span>
              </div>
              <div className="text-xs font-mono text-slate-400">
              SYNC: <span className="text-blue-500 animate-pulse">LIVE</span>
              </div>
          </div>
        </header>

        {/* Input Area */}
        <div className="max-w-3xl mx-auto mb-6 w-full flex gap-2">
          <input
            type="text"
            value={instruction}
            onChange={(e) => setInstruction(e.target.value)}
            placeholder="司令官、指示を入力してください..."
            className="flex-1 p-3 border border-slate-200 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
            onKeyDown={(e) => {
              if (e.nativeEvent.isComposing) return;
              if (e.key === 'Enter') startMission();
            }}
          />
          <button
            onClick={startMission}
            disabled={loading}
            className="bg-blue-600 text-white px-6 py-3 rounded-lg font-bold hover:bg-blue-700 disabled:opacity-50 transition-all text-sm tracking-wider"
          >
            {loading ? "DEPLOYING..." : "EXECUTE"}
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 min-h-0 p-6 pt-0 grid grid-cols-1 lg:grid-cols-4 gap-6">
        
        {/* Left Column: History & Logs */}
        <div className="lg:col-span-1 flex flex-col gap-4 h-full min-h-0">
            <div className="bg-white border border-slate-200 rounded-xl shadow-sm flex flex-col flex-1 min-h-0 overflow-hidden">
                <div className="p-3 border-b border-slate-100 bg-slate-50 text-xs font-bold text-slate-500 uppercase tracking-wider flex-none">
                    Mission History
                </div>
                <div className="overflow-y-auto flex-1 p-2 space-y-2 custom-scrollbar">
                    {history.length === 0 && (
                        <div className="text-center text-xs text-slate-400 py-4">No Missions Yet</div>
                    )}
                    {history.map((m: any) => {
                        const isSelected = m.id === missionData.id || m.id === missionData.mission_id;
                        return (
                            <button
                                key={m.id}
                                onClick={() => handleSelectMission(m)}
                                className={`w-full text-left p-3 rounded-lg text-xs transition-all border ${
                                    isSelected 
                                    ? "bg-blue-50 border-blue-200 ring-1 ring-blue-300" 
                                    : "bg-white border-slate-100 hover:bg-slate-50 hover:border-slate-300"
                                }`}
                            >
                                <div className="font-bold truncate mb-1 text-slate-700">
                                    {m.instruction || "No Instruction"}
                                </div>
                                <div className="flex justify-between items-center text-slate-400 font-mono text-[10px]">
                                    <span>{new Date(m.created_at || Date.now()).toLocaleTimeString()}</span>
                                    <span className={m.status === 'done' ? "text-green-600" : "text-amber-500"}>
                                        {m.status?.toUpperCase()}
                                    </span>
                                </div>
                            </button>
                        );
                    })}
                </div>
            </div>

            <div className="bg-black text-green-400 p-4 rounded-xl font-mono text-xs overflow-hidden shadow-xl border border-slate-800 flex flex-col flex-1 min-h-0 transition-all">
                <div className="flex justify-between items-center mb-2 border-b border-slate-800 pb-2 flex-none">
                    <h3 className="text-slate-500 uppercase">Ghost_Logs</h3>
                    <div className={`w-2 h-2 rounded-full ${loading ? "bg-amber-500 animate-ping" : "bg-green-500"}`}></div>
                </div>
                <ul className="space-y-2 flex-1 overflow-y-auto pr-2 custom-scrollbar">
                    {(missionData.logs || []).map((log: string, i: number) => (
                    <li key={i} className="flex gap-2 leading-relaxed opacity-90">
                        <span className="text-slate-600 select-none">[{i.toString().padStart(2, '0')}]</span>
                        <span>{log}</span>
                    </li>
                    ))}
                </ul>
            </div>
        </div>

        {/* Right Column: Kanban Area */}
        {/* ★修正: bg-white や border を削除。h-full のみ残します */}
        <div className="lg:col-span-3 h-full min-h-0">
             <LivingKanban initialTasks={missionData.tasks || []} />
        </div>
      </div>
    </main>
  );
}
