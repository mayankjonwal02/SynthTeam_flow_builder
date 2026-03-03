"use client";

import { Handle, Position, useReactFlow } from "reactflow";
import { useCallback, useState } from "react";
import { ShieldCheck } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import NodeWrapper from "./NodeWrapper";
import FieldModeInput, { FieldMode } from "./FieldModeInput";

const AUTH_TYPES = ["api_key"] as const;

interface ModeValue { mode: FieldMode; value: string; }

export default function AuthNodeNode({ id, data, selected }: any) {
  const { setNodes } = useReactFlow();
  const [nodeName, setNodeName] = useState(data.label || "Auth Gate");
  const [authType, setAuthType] = useState<string>(data.config?.type || "api_key");
  const [headerName, setHeaderName] = useState<ModeValue>({
    mode: data.config?.header_name_mode || "static",
    value: data.config?.header_name || "x-api-key",
  });

  const syncConfig = useCallback(
    (t: string, h: ModeValue, lbl?: string) => {
      setNodes((nds) =>
        nds.map((node) =>
          node.id === id
            ? {
                ...node,
                data: {
                  ...node.data,
                  label: lbl ?? node.data.label,
                  component: "auth_node",
                  config: { ...node.data.config, type: t, header_name: h.value, header_name_mode: h.mode },
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
            ? { ...node, data: { ...node.data, component: "auth_node", config: { ...node.data.config, type: authType, header_name: headerName.value, header_name_mode: headerName.mode } } }
            : node
        )
      );
    });
  }

  const handleTypeChange = (v: string) => { setAuthType(v); syncConfig(v, headerName); };
  const handleNameChange = (n: string) => { setNodeName(n); syncConfig(authType, headerName, n); };

  return (
    <NodeWrapper id={id} name={nodeName} onNameChange={handleNameChange} accentColor="red">
      <div className={`bg-[#1a1a2e] border rounded-xl shadow-2xl shadow-red-500/5 w-80 relative overflow-visible ${selected ? "border-red-400 ring-1 ring-red-400/30" : "border-red-500/30"}`}>
        <div className="flex items-center gap-2 px-4 py-3 bg-red-500/10 border-b border-red-500/20">
          <ShieldCheck className="w-4 h-4 text-red-400" />
          <span className="text-sm font-semibold text-red-300">{nodeName}</span>
          <Badge variant="outline" className="ml-auto text-[10px] px-1.5 py-0 bg-red-500/20 text-red-400 border-red-500/30">
            {authType}
          </Badge>
        </div>
        <div className="p-4 space-y-3">
          <div>
            <div className="text-[10px] uppercase tracking-widest text-white/30 font-semibold mb-1.5">Auth Type</div>
            <select
              value={authType}
              onChange={(e) => handleTypeChange(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-red-500/50"
            >
              {AUTH_TYPES.map((t) => (
                <option key={t} value={t} className="bg-[#1a1a2e]">{t}</option>
              ))}
            </select>
          </div>
          <div>
            <div className="text-[10px] uppercase tracking-widest text-white/30 font-semibold mb-1.5">Header Name</div>
            <FieldModeInput
              mode={headerName.mode}
              value={headerName.value}
              onModeChange={(mode) => { const u = { mode, value: "" }; setHeaderName(u); syncConfig(authType, u); }}
              onValueChange={(value) => { const u = { ...headerName, value }; setHeaderName(u); syncConfig(authType, u); }}
              placeholder={{ static: "x-api-key", input: "input.headerKey", expression: "input.config.authHeader" }}
            />
          </div>
          <div className="bg-white/5 rounded-lg px-3 py-2">
            <p className="text-xs text-white/50 leading-relaxed">
              Validates the API key from the request header. Blocks execution if invalid.
            </p>
          </div>
        </div>
        <Handle type="target" id="input" position={Position.Left} className="!bg-red-500 !border-red-300 !w-3 !h-3" title="Input" />
        <span className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-full pr-2 text-[9px] font-semibold uppercase tracking-wider text-white/50 whitespace-nowrap pointer-events-none">Input</span>
        <Handle type="source" id="output" position={Position.Right} className="!bg-red-500 !border-red-300 !w-3 !h-3" title="Output" />
        <span className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-full pl-2 text-[9px] font-semibold uppercase tracking-wider text-white/50 whitespace-nowrap pointer-events-none">Output</span>
      </div>
    </NodeWrapper>
  );
}
