"use client";

import { Handle, Position, useReactFlow } from "reactflow";
import { useCallback, useState } from "react";
import { FileSearch, Plus, Trash2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import NodeWrapper from "./NodeWrapper";

export default function HeaderExtractorNode({ id, data, selected }: any) {
  const { setNodes } = useReactFlow();
  const [nodeName, setNodeName] = useState(data.label || "Header Extractor");
  const [headers, setHeaders] = useState<string[]>(data.config?.headers || []);
  const [newHeader, setNewHeader] = useState("");

  const syncConfig = useCallback(
    (h: string[], lbl?: string) => {
      setNodes((nds) =>
        nds.map((node) =>
          node.id === id
            ? {
                ...node,
                data: {
                  ...node.data,
                  label: lbl ?? node.data.label,
                  component: "header_extractor",
                  config: { ...node.data.config, headers: h },
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
            ? { ...node, data: { ...node.data, component: "header_extractor", config: { ...node.data.config, headers } } }
            : node
        )
      );
    });
  }

  const addHeader = () => {
    if (!newHeader.trim() || headers.includes(newHeader.trim().toLowerCase())) return;
    const updated = [...headers, newHeader.trim().toLowerCase()];
    setHeaders(updated);
    syncConfig(updated);
    setNewHeader("");
  };

  const removeHeader = (idx: number) => {
    const updated = headers.filter((_, i) => i !== idx);
    setHeaders(updated);
    syncConfig(updated);
  };

  const handleNameChange = (n: string) => {
    setNodeName(n);
    syncConfig(headers, n);
  };

  return (
    <NodeWrapper id={id} name={nodeName} onNameChange={handleNameChange} accentColor="slate">
      <div className={`bg-[#1a1a2e] border rounded-xl shadow-2xl shadow-slate-500/5 w-72 overflow-hidden ${selected ? "border-slate-400 ring-1 ring-slate-400/30" : "border-slate-500/30"}`}>
        <div className="flex items-center gap-2 px-4 py-3 bg-slate-500/10 border-b border-slate-500/20">
          <FileSearch className="w-4 h-4 text-slate-400" />
          <span className="text-sm font-semibold text-slate-300">{nodeName}</span>
          <Badge variant="outline" className="ml-auto text-[10px] px-1.5 py-0 bg-slate-500/20 text-slate-400 border-slate-500/30">
            {headers.length}
          </Badge>
        </div>
        <div className="p-4 space-y-2">
          <div className="text-[10px] uppercase tracking-widest text-white/30 font-semibold">Headers to Extract</div>
          {headers.map((h, i) => (
            <div key={i} className="flex items-center gap-2 bg-white/5 rounded-lg px-3 py-1.5 group">
              <span className="text-xs text-white/80 flex-1 font-mono">{h}</span>
              <button onClick={() => removeHeader(i)} className="opacity-0 group-hover:opacity-100 transition-opacity text-red-400 hover:text-red-300">
                <Trash2 className="w-3 h-3" />
              </button>
            </div>
          ))}
          <div className="flex gap-1.5">
            <input
              value={newHeader}
              onChange={(e) => setNewHeader(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && addHeader()}
              placeholder="header-name"
              className="flex-1 bg-white/5 border border-white/10 rounded-md px-2 py-1 text-xs text-white placeholder-white/25 focus:outline-none focus:border-slate-500/50 font-mono"
            />
            <button onClick={addHeader} className="bg-slate-500/20 hover:bg-slate-500/30 text-slate-400 rounded-md px-2 transition-colors">
              <Plus className="w-3 h-3" />
            </button>
          </div>
        </div>
        <Handle type="target" position={Position.Left} className="!bg-slate-500 !border-slate-300 !w-3 !h-3" />
        <Handle type="source" position={Position.Right} className="!bg-slate-500 !border-slate-300 !w-3 !h-3" />
      </div>
    </NodeWrapper>
  );
}
