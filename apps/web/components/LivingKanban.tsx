"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  DndContext,
  DragOverlay,
  useDraggable,
  useDroppable,
  DragEndEvent,
  DragStartEvent,
  closestCorners,
} from "@dnd-kit/core";

// --- 型定義 ---
type Task = {
  id: string;
  title: string;
  status: string;
  assignee?: string;
  energy: number;
};

type Props = {
  initialTasks: Task[];
};

const COLUMNS = [
  { id: "planning", title: "Planning" },
  { id: "working", title: "Working" },
  { id: "done", title: "Done" },
];

// --- サブコンポーネント: ドラッグ可能なカード ---
function DraggableCard({ task }: { task: Task }) {
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
    id: task.id,
    data: task,
  });

  return (
    <div
      ref={setNodeRef}
      {...listeners}
      {...attributes}
      className={`relative p-4 rounded-lg shadow-sm border transition-all cursor-grab active:cursor-grabbing group
        ${isDragging ? "opacity-30 border-blue-400" : "bg-white border-slate-100 hover:shadow-md"}
      `}
    >
      {/* タチコマ風ヘッダー */}
      <div className="flex justify-between items-start mb-2">
        <div className="flex items-center gap-2">
          {task.assignee && (
            <div
              className={`w-2 h-2 rounded-full animate-pulse ${
                task.status === "working" ? "bg-blue-500" : "bg-slate-300"
              }`}
            />
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

      {/* Workingエフェクト */}
      {task.status === "working" && !isDragging && (
        <div className="mt-3 h-1 w-full bg-slate-100 rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-blue-400"
            initial={{ x: "-100%" }}
            animate={{ x: "100%" }}
            transition={{ repeat: Infinity, duration: 1.5, ease: "linear" }}
          />
        </div>
      )}
    </div>
  );
}

// --- サブコンポーネント: ドロップ可能なカラム ---
function DroppableColumn({ col, tasks }: { col: { id: string; title: string }; tasks: Task[] }) {
  const { setNodeRef } = useDroppable({
    id: col.id,
  });

  return (
    <div
      ref={setNodeRef}
      className="bg-slate-100/50 rounded-xl p-4 border border-slate-200 backdrop-blur-sm flex flex-col gap-3 min-h-[200px]"
    >
      {/* カラムヘッダー */}
      <div className="flex justify-between items-center mb-1">
        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest">
          {col.title}
        </h3>
        <span className="text-xs font-mono bg-slate-200 text-slate-500 px-2 py-0.5 rounded-full">
          {tasks.length}
        </span>
      </div>

      {/* タスクリスト */}
      <div className="flex flex-col gap-3 flex-1">
        {tasks.map((task) => (
          <DraggableCard key={task.id} task={task} />
        ))}
        {tasks.length === 0 && (
           <div className="h-24 border-2 border-dashed border-slate-200 rounded-lg flex items-center justify-center">
             <span className="text-xs text-slate-300">NO SIGNAL</span>
           </div>
        )}
      </div>
    </div>
  );
}

// --- メインコンポーネント ---
export function LivingKanban({ initialTasks }: Props) {
  // ローカルステートでタスクを管理（ドラッグ操作で書き換えるため）
  const [tasks, setTasks] = useState<Task[]>(initialTasks);
  const [activeId, setActiveId] = useState<string | null>(null);

  // 親から新しいタスクが来たら同期する
  useEffect(() => {
    setTasks(initialTasks);
  }, [initialTasks]);

  // ドラッグ開始
  const handleDragStart = (event: DragStartEvent) => {
    setActiveId(event.active.id as string);
  };

  // ドラッグ終了（ドロップ）
  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      // ドロップ先のカラムIDを取得
      // ※今回はカラム自体をDroppableにしているので、over.idがそのままstatusになる
      const newStatus = over.id as string;

      setTasks((prev) =>
        prev.map((t) => {
          if (t.id === active.id) {
            // ステータス変更ロジック
            // もしAIが担当していたら、ユーザー介入としてAssigneeを変更してもよい
            return { ...t, status: newStatus };
          }
          return t;
        })
      );
      
      console.log(`[COMMANDER OVERRIDE] Task ${active.id} moved to ${newStatus}`);
    }
    setActiveId(null);
  };

  const activeTask = tasks.find((t) => t.id === activeId);

  return (
    <DndContext
      collisionDetection={closestCorners}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
    >
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 h-full">
        {COLUMNS.map((col) => (
          <DroppableColumn
            key={col.id}
            col={col}
            tasks={tasks.filter((t) => t.status === col.id)}
          />
        ))}
      </div>

      {/* ドラッグ中の浮遊カード（DragOverlay） */}
      <DragOverlay>
        {activeTask ? (
          <div className="opacity-90 rotate-3 scale-105 transform cursor-grabbing">
            <div className="p-4 bg-white rounded-lg shadow-xl border-2 border-blue-400">
               <h4 className="text-sm font-bold text-slate-800">{activeTask.title}</h4>
               <p className="text-xs text-blue-500 font-bold mt-1">MOVING...</p>
            </div>
          </div>
        ) : null}
      </DragOverlay>
    </DndContext>
  );
}
