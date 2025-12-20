"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  DndContext,
  DragOverlay,
  useDraggable,
  useDroppable,
  DragEndEvent,
  DragStartEvent,
  closestCorners,
} from "@dnd-kit/core";

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

// --- Draggable Card ---
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
      className={`relative p-3 mb-3 rounded-lg shadow-sm border transition-all cursor-grab active:cursor-grabbing group
        ${isDragging ? "opacity-30 border-blue-400" : "bg-white border-slate-200 hover:shadow-md hover:border-blue-300"}
      `}
    >
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
        <div className="flex items-center gap-1">
            <span className="text-[10px] text-slate-300">⚡</span>
            <span className="text-[10px] font-mono text-slate-400">
                {task.energy}
            </span>
        </div>
      </div>
      <h4 className="text-xs font-bold text-slate-700 leading-tight">
        {task.title}
      </h4>
      {task.status === "working" && !isDragging && (
        <div className="mt-2 h-1 w-full bg-slate-100 rounded-full overflow-hidden">
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

// --- Droppable Column ---
function DroppableColumn({ col, tasks }: { col: { id: string; title: string }; tasks: Task[] }) {
  const { setNodeRef } = useDroppable({
    id: col.id,
  });

  // ★修正: パネル自体に背景色とボーダーを持たせ、完全に独立したカードのように見せます
  const bgColors: Record<string, string> = {
    planning: "bg-white",
    working: "bg-blue-50/30",
    done: "bg-green-50/30"
  };

  return (
    <div
      ref={setNodeRef}
      // ★修正: h-full で高さいっぱいに。border, rounded-xl をここで適用。
      className={`flex flex-col h-full overflow-hidden border border-slate-200 rounded-xl shadow-sm ${bgColors[col.id]}`}
    >
      {/* Header */}
      <div className="p-3 border-b border-slate-100 flex justify-between items-center flex-none bg-white/50">
        <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">
          {col.title}
        </h3>
        <span className="text-[10px] font-mono text-slate-400 bg-slate-100 px-2 py-0.5 rounded-full">
          {tasks.length}
        </span>
      </div>

      {/* Task List */}
      <div className="flex-1 overflow-y-auto p-3 custom-scrollbar flex flex-col">
        {tasks.map((task) => (
          <DraggableCard key={task.id} task={task} />
        ))}
        
        {/* タスクが無い時は、余白全体を使って「NO TASKS」を中央表示 */}
        {tasks.length === 0 && (
            <div className="flex-1 flex items-center justify-center border-2 border-dashed border-slate-100 rounded-lg m-2 opacity-50">
               <span className="text-[10px] text-slate-300 tracking-widest">NO TASKS</span>
            </div>
        )}
      </div>
    </div>
  );
}

// --- Main Component ---
export function LivingKanban({ initialTasks }: Props) {
  const [tasks, setTasks] = useState<Task[]>(initialTasks);
  const [activeId, setActiveId] = useState<string | null>(null);

  useEffect(() => {
    setTasks(initialTasks);
  }, [initialTasks]);

  const handleDragStart = (event: DragStartEvent) => {
    setActiveId(event.active.id as string);
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    if (over && active.id !== over.id) {
      const newStatus = over.id as string;
      setTasks((prev) =>
        prev.map((t) => {
          if (t.id === active.id) {
            return { ...t, status: newStatus };
          }
          return t;
        })
      );
      try {
        await fetch(`http://localhost:8000/mission/tasks/${active.id}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ status: newStatus }),
        });
      } catch (e) {
        console.error("Failed to persist task status:", e);
      }
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
      {/* ★修正: gap-4 を復活させ、3枚のパネルが並んでいるようなデザインにします */}
      <div className="h-full grid grid-cols-1 md:grid-cols-3 gap-4">
        {COLUMNS.map((col) => (
          <DroppableColumn
            key={col.id}
            col={col}
            tasks={tasks.filter((t) => t.status === col.id)}
          />
        ))}
      </div>

      <DragOverlay>
        {activeTask ? (
          <div className="opacity-90 rotate-2 scale-105 cursor-grabbing w-[280px]">
            <div className="p-3 bg-white rounded-lg shadow-2xl border-2 border-blue-500">
               <h4 className="text-xs font-bold text-slate-800">{activeTask.title}</h4>
            </div>
          </div>
        ) : null}
      </DragOverlay>
    </DndContext>
  );
}
