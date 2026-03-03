"use client";

import { Handle, Position, useReactFlow } from "reactflow";
import { useCallback, useState } from "react";
import { FileSearch, Plus, Trash2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import NodeWrapper from "./NodeWrapper";
import FieldModeInput, { FieldMode } from "./FieldModeInput";

interface HeaderEntry {
  name: string;
  mode: FieldMode;
  value: string;
}

export default function HeaderExtractorNode({ id, data, selected }: any) {
  const { setNodes } = useReactFlow();
  const [nodeName, setNodeName] = useState(data.label || "Header Extractor");
  const [headers, setHeaders] = useState<HeaderEntry[]>(() => {
    if (data.config?.header_mappings) return data.config.header_mappings;
    const legacy = data.config?.headers || [];
    return legacy.map((h: string) => ({ name: h, mode: "static" as FieldMode, value: h }));
  });
  const [newHeader, setNewHeader] = useState("");

  const syncConfig = useCallback(
    (h: HeaderEntry[], lbl?: string) => {
      const legacyHeaders = h.map((e) => e.value || e.name);
      setNodes((nds) =>
        nds.map((node) =>
          node.id === id
            ? {
                ...node,
                data: {
                  ...node.data,
                  label: lbl ?? node.data.label,
                  component: "header_extractor",
                  config: { ...node.data.config, headers: legacyHeaders, header_mappings: h },
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
            ? { ...node, data: { ...node.data, component: "header_extractor", config: { ...node.data.config, headers: headers.map(e => e.value || e.name), header_mappings: headers } } }
            : node
        )
      );
    });
  }

  const addHeader = () => {
    if (!newHeader.trim()) return;
    const updated = [...headers, { name: newHeader.trim().toLowerCase(), mode: "static" as FieldMode, value: newHeader.trim().toLowerCase() }];
    setHeaders(updated);
    syncConfig(updated);
    setNewHeader("");
  };

  const removeHeader = (idx: number) => {
    const updated = headers.filter((_, i) => i !== idx);
    setHeaders(updated);
    syncConfig(updated);
  };

  const updateHeader = (idx: number, patch: Partial<HeaderEntry>) => {
    const updated = headers.map((h, i) => (i === idx ? { ...h, ...patch } : h));
    setHeaders(updated);
    syncConfig(updated);
  };

  const handleNameChange = (n: string) => { setNodeName(n); syncConfig(headers, n); };

  return (
    <NodeWrapper id={id} name={nodeName} onNameChange={handleNameChange} accentColor="slate">
      <div className={`bg-[#1a1a2e] border rounded-xl shadow-2xl shadow-slate-500/5 w-80 relative overflow-visible ${selected ? "border-slate-400 ring-1 ring-slate-400/30" : "border-slate-500/30"}`}>
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
            <div key={i} className="bg-white/[0.03] border border-white/[0.06] rounded-lg p-2 space-y-1.5 group">
              <div className="flex items-center gap-2">
                <span className="text-[10px] text-white/70 font-mono font-medium flex-1">{h.name}</span>
                <button onClick={() => removeHeader(i)} className="opacity-0 group-hover:opacity-100 transition-opacity text-red-400 hover:text-red-300">
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
              <FieldModeInput
                mode={h.mode}
                value={h.value}
                onModeChange={(mode) => updateHeader(i, { mode, value: "" })}
                onValueChange={(value) => updateHeader(i, { value })}
                placeholder={{ static: "x-custom-header", input: "input.headerName", expression: "input.config.header" }}
              />
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
        <Handle type="target" id="input" position={Position.Left} className="!bg-slate-500 !border-slate-300 !w-3 !h-3" title="Input" />
        <span className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-full pr-2 text-[9px] font-semibold uppercase tracking-wider text-white/50 whitespace-nowrap pointer-events-none">Input</span>
        <Handle type="source" id="output" position={Position.Right} className="!bg-slate-500 !border-slate-300 !w-3 !h-3" title="Output" />
        <span className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-full pl-2 text-[9px] font-semibold uppercase tracking-wider text-white/50 whitespace-nowrap pointer-events-none">Output</span>
      </div>
    </NodeWrapper>
  );
}
