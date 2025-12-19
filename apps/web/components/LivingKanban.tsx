"use client";

import { motion, AnimatePresence } from "framer-motion";

type Task = {
  id: string;
  title: string;
  status: string;
  assignee?: string;
  energy: number;
};

type Props = {
  tasks: Task[];
};

const COLUMNS = [
  { id: "planning", title: "Planning" },
  { id: "working", title: "Working" },
  { id: "done", title: "Done" },
];

export function LivingKanban({ tasks }: Props) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 h-full">
      {COLUMNS.map((col) => {
        // カラムごとのタスクをフィルタリング
        const colTasks = tasks.filter((t) => t.status === col.id);

        return (
          <div key={col.id} className="bg-slate-100/50 rounded-xl p-4 border border-slate-200 backdrop-blur-sm">
            {/* カラムヘッダー */}
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest">
                {col.title}
              </h3>
              <span className="text-xs font-mono bg-slate-200 text-slate-500 px-2 py-0.5 rounded-full">
                {colTasks.length}
              </span>
            </div>

            {/* タスクリスト（アニメーション付き） */}
            <div className="space-y-3">
              <AnimatePresence mode="popLayout">
                {colTasks.map((task) => (
                  <motion.div
                    key={task.id}
                    layoutId={task.id} // これがあるだけで別カラムへの移動がアニメーションする
                    initial={{ opacity: 0, y: 20, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.9 }}
                    transition={{ type: "spring", stiffness: 300, damping: 30 }}
                    className="bg-white p-4 rounded-lg shadow-sm border border-slate-100 group hover:shadow-md transition-shadow cursor-grab active:cursor-grabbing"
                  >
                    {/* タチコマ風アイコン */}
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex items-center gap-2">
                        {task.assignee && (
                          <div className={`w-2 h-2 rounded-full animate-pulse ${
                            task.status === 'working' ? 'bg-blue-500' : 'bg-slate-300'
                          }`} />
                        )}
                        <span className="text-[10px] font-bold text-slate-400 uppercase">
                          {task.assignee || "UNASSIGNED"}
                        </span>
                      </div>
                      <span className="text-[10px] font-mono text-slate-400">
                        ${task.energy}
                      </span>
                    </div>

                    <h4 className="text-sm font-bold text-slate-700 leading-tight">
                      {task.title}
                    </h4>

                    {/* 作業中のエフェクト（Workingのみ） */}
                    {task.status === 'working' && (
                      <div className="mt-3 h-1 w-full bg-slate-100 rounded-full overflow-hidden">
                        <motion.div 
                          className="h-full bg-blue-400"
                          initial={{ x: "-100%" }}
                          animate={{ x: "100%" }}
                          transition={{ repeat: Infinity, duration: 1.5, ease: "linear" }}
                        />
                      </div>
                    )}
                  </motion.div>
                ))}
              </AnimatePresence>
              
              {colTasks.length === 0 && (
                <div className="h-24 border-2 border-dashed border-slate-200 rounded-lg flex items-center justify-center">
                  <span className="text-xs text-slate-300">NO SIGNAL</span>
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
