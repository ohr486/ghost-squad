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
    logs: INITIAL_LOGS,
    tasks: []
  });
  const [loading, setLoading] = useState(false);

  // --- 監視システム (Polling Hook) ---
  useEffect(() => {
    // 2秒ごとに最新情報を本部(API)に取りに行く
    const interval = setInterval(async () => {
      try {
        const res = await fetch("http://localhost:8000/mission/current");
        if (res.ok) {
          const data = await res.json();
          // データが存在し、かつ新しいミッションIDであれば更新
          if (data && data.mission_id) {
             // 簡易的な比較（実際はIDなどで厳密にやるが、今回はデータがあれば上書き）
             setMissionData((prev: any) => {
               // 既に同じログ量なら更新しない（ちらつき防止）
               if (prev.logs.length === data.logs.length && prev.tasks.length === data.tasks.length) {
                 return prev;
               }
               return data;
             });
          }
        }
      } catch (e) {
        // 接続エラーは無視（コンソールのみ）
        console.error("Sync Error:", e);
      }
    }, 2000); // 2000ms = 2秒間隔

    return () => clearInterval(interval);
  }, []);

  // --- 手動送信（ブラウザから） ---
  const startMission = async () => {
    setLoading(true);
    setMissionData((prev: any) => ({
      ...prev,
      logs: [...prev.logs, ">>> TRANSMITTING ORDERS TO SQUAD..."]
    }));

    try {
      // POSTすると、API側で latest_mission_state が更新される
      // その後、上記のPollingで自動的に画面も更新されるが、
      // ユーザー体験向上のためここでもセットしておく
      const res = await fetch("http://localhost:8000/mission/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ instruction }),
      });
      const data = await res.json();
      setMissionData(data);
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
            SYNC: <span className="text-blue-500 animate-pulse">LIVE</span>
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
	  onKeyDown={(e) => {
            // IME変換中(isComposingがtrue)なら何もしない
            if (e.nativeEvent.isComposing) return;
            
            if (e.key === 'Enter') {
              startMission();
            }
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

      {/* Mission Result */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 flex-1">
        {/* Logs */}
        <div className="lg:col-span-1 bg-black text-green-400 p-4 rounded-xl font-mono text-xs overflow-y-auto shadow-xl border border-slate-800 flex flex-col h-[600px] lg:h-auto transition-all">
          <div className="flex justify-between items-center mb-2 border-b border-slate-800 pb-2">
            <h3 className="text-slate-500 uppercase">Ghost_Logs</h3>
            <div className="w-2 h-2 bg-green-500 rounded-full animate-ping"></div>
          </div>
          <ul className="space-y-2 flex-1 overflow-y-auto pr-2 custom-scrollbar">
            {missionData.logs.map((log: string, i: number) => (
              <li key={i} className="flex gap-2 leading-relaxed opacity-90 animate-in fade-in slide-in-from-left-2">
                <span className="text-slate-600 select-none">[{i.toString().padStart(2, '0')}]</span>
                <span>{log}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Kanban */}
        <div className="lg:col-span-3 h-[600px] lg:h-auto">
          <LivingKanban initialTasks={missionData.tasks} />
        </div>
      </div>
    </main>
  );
}

