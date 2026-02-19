"use client";

import { Handle, Position, useReactFlow } from "reactflow";
import { useCallback, useState } from "react";
import { Route, Plus, Trash2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import NodeWrapper from "./NodeWrapper";

export default function SwitchCaseNode({ id, data, selected }: any) {
  const { setNodes } = useReactFlow();
  const [nodeName, setNodeName] = useState(data.label || "Switch / Case");
  const [field, setField] = useState<string>(data.config?.field || "");
  const [cases, setCases] = useState<string[]>(data.config?.cases || []);
  const [newCase, setNewCase] = useState("");

  const syncConfig = useCallback(
    (f: string, c: string[], lbl?: string) => {
      setNodes((nds) =>
        nds.map((node) =>
          node.id === id
            ? {
                ...node,
                data: {
                  ...node.data,
                  label: lbl ?? node.data.label,
                  component: "switch_case",
                  config: { ...node.data.config, field: f, cases: c },
                },
              }
            : node
        )
      );
    },
    [id, setNodes]
  );

  if (!data.component) {
    queueMicrotask(() => {
      setNodes((nds) =>
        nds.map((node) =>
          node.id === id
            ? { ...node, data: { ...node.data, component: "switch_case", config: { ...node.data.config, field, cases } } }
            : node
        )
      );
    });
  }

  const handleFieldChange = (v: string) => { setField(v); syncConfig(v, cases); };

  const addCase = () => {
    if (!newCase.trim() || cases.includes(newCase.trim())) return;
    const updated = [...cases, newCase.trim()];
    setCases(updated);
    syncConfig(field, updated);
    setNewCase("");
  };

  const removeCase = (idx: number) => {
    const updated = cases.filter((_, i) => i !== idx);
    setCases(updated);
    syncConfig(field, updated);
  };

  const handleNameChange = (n: string) => { setNodeName(n); syncConfig(field, cases, n); };

  return (
    <NodeWrapper id={id} name={nodeName} onNameChange={handleNameChange} accentColor="violet">
      <div className={`bg-[#1a1a2e] border rounded-xl shadow-2xl shadow-violet-500/5 w-72 overflow-hidden ${selected ? "border-violet-400 ring-1 ring-violet-400/30" : "border-violet-500/30"}`}>
        <div className="flex items-center gap-2 px-4 py-3 bg-violet-500/10 border-b border-violet-500/20">
          <Route className="w-4 h-4 text-violet-400" />
          <span className="text-sm font-semibold text-violet-300">{nodeName}</span>
          <Badge variant="outline" className="ml-auto text-[10px] px-1.5 py-0 bg-violet-500/20 text-violet-400 border-violet-500/30">
            {cases.length} case{cases.length !== 1 ? "s" : ""}
          </Badge>
        </div>
        <div className="p-4 space-y-3">
          <div>
            <div className="text-[10px] uppercase tracking-widest text-white/30 font-semibold mb-1.5">Switch Field</div>
            <input
              value={field}
              onChange={(e) => handleFieldChange(e.target.value)}
              placeholder="e.g. status"
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-white/30 focus:outline-none focus:border-violet-500/50 font-mono"
            />
          </div>
          <div className="space-y-2">
            <div className="text-[10px] uppercase tracking-widest text-white/30 font-semibold">Case Values</div>
            {cases.map((c, i) => (
              <div key={i} className="flex items-center gap-2 bg-white/5 rounded-lg px-3 py-1.5 group">
                <span className="text-xs text-white/80 flex-1 font-mono">{c}</span>
                <button onClick={() => removeCase(i)} className="opacity-0 group-hover:opacity-100 transition-opacity text-red-400 hover:text-red-300">
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
            ))}
            <div className="flex gap-1.5">
              <input
                value={newCase}
                onChange={(e) => setNewCase(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && addCase()}
                placeholder="case value"
                className="flex-1 bg-white/5 border border-white/10 rounded-md px-2 py-1 text-xs text-white placeholder-white/25 focus:outline-none focus:border-violet-500/50 font-mono"
              />
              <button onClick={addCase} className="bg-violet-500/20 hover:bg-violet-500/30 text-violet-400 rounded-md px-2 transition-colors">
                <Plus className="w-3 h-3" />
              </button>
            </div>
          </div>
          <div className="bg-white/5 rounded-lg px-3 py-2">
            <p className="text-[10px] text-white/40 leading-relaxed">
              Connect edges with <span className="text-violet-400 font-mono">condition: "value"</span> matching each case.
            </p>
          </div>
        </div>
        <Handle type="target" position={Position.Left} className="!bg-violet-500 !border-violet-300 !w-3 !h-3" />
        <Handle type="source" position={Position.Right} className="!bg-violet-500 !border-violet-300 !w-3 !h-3" />
      </div>
    </NodeWrapper>
  );
}
