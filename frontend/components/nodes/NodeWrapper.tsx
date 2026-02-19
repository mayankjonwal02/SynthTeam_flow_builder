"use client";

import { useReactFlow } from "reactflow";
import { useState } from "react";
import { X, Pencil, Check } from "lucide-react";

/**
 * Wraps every custom node with:
 *  • A floating delete (X) button — visible on hover
 *  • An editable node name in the header
 */
export default function NodeWrapper({
  id,
  name,
  onNameChange,
  accentColor = "white",   // tailwind color token: blue, amber, emerald…
  children,
}: {
  id: string;
  name: string;
  onNameChange: (n: string) => void;
  accentColor?: string;
  children: React.ReactNode;
}) {
  const { setNodes, setEdges } = useReactFlow();
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(name);

  const deleteNode = (e: React.MouseEvent) => {
    e.stopPropagation();
    setNodes((nds) => nds.filter((n) => n.id !== id));
    setEdges((eds) => eds.filter((e) => e.source !== id && e.target !== id));
  };

  const commitName = () => {
    const trimmed = draft.trim() || name;
    setDraft(trimmed);
    onNameChange(trimmed);
    setEditing(false);
  };

  return (
    <div className="relative group/node">
      {/* ── floating delete button ── */}
      <button
        onClick={deleteNode}
        className="absolute -top-2.5 -right-2.5 z-50 w-5 h-5 rounded-full bg-red-500/90 text-white flex items-center justify-center opacity-0 group-hover/node:opacity-100 transition-opacity shadow-lg hover:bg-red-400 hover:scale-110"
      >
        <X className="w-3 h-3" />
      </button>

      {/* ── editable name overlay (sits below the node header icon) ── */}
      <div className="absolute top-[3px] left-9 right-14 z-40 flex items-center gap-1">
        {editing ? (
          <div className="flex items-center gap-1 w-full">
            <input
              autoFocus
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") commitName();
                if (e.key === "Escape") { setDraft(name); setEditing(false); }
              }}
              onBlur={commitName}
              className="flex-1 bg-black/40 border border-white/20 rounded px-1.5 py-0.5 text-[11px] text-white font-semibold focus:outline-none focus:border-white/40 min-w-0"
            />
          </div>
        ) : (
          <button
            onDoubleClick={() => setEditing(true)}
            className="flex items-center gap-1 text-[11px] truncate max-w-full"
            title="Double-click to rename"
          >
            <span className="truncate text-white/60 font-medium">{name}</span>
            <Pencil className="w-2.5 h-2.5 text-white/20 opacity-0 group-hover/node:opacity-100 transition-opacity shrink-0" />
          </button>
        )}
      </div>

      {children}
    </div>
  );
}
