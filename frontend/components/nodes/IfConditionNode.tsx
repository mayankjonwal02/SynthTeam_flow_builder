"use client";

import { Handle, Position, useReactFlow } from "reactflow";
import { useCallback, useState } from "react";
import { GitBranch } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import NodeWrapper from "./NodeWrapper";

const OPERATORS = ["==", "!=", ">", "<", ">=", "<="] as const;

export default function IfConditionNode({ id, data, selected }: any) {
  const { setNodes } = useReactFlow();
  const [nodeName, setNodeName] = useState(data.label || "If Condition");
  const [field, setField] = useState<string>(data.config?.field || "");
  const [operator, setOperator] = useState<string>(data.config?.operator || "==");
  const [value, setValue] = useState<string>(String(data.config?.value ?? ""));

  const syncConfig = useCallback(
    (f: string, op: string, v: string, lbl?: string) => {
      setNodes((nds) =>
        nds.map((node) =>
          node.id === id
            ? {
                ...node,
                data: {
                  ...node.data,
                  label: lbl ?? node.data.label,
                  component: "if_condition",
                  config: { ...node.data.config, field: f, operator: op, value: v },
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
            ? { ...node, data: { ...node.data, component: "if_condition", config: { ...node.data.config, field, operator, value } } }
            : node
        )
      );
    });
  }

  const handleFieldChange = (v: string) => { setField(v); syncConfig(v, operator, value); };
  const handleOperatorChange = (v: string) => { setOperator(v); syncConfig(field, v, value); };
  const handleValueChange = (v: string) => { setValue(v); syncConfig(field, operator, v); };
  const handleNameChange = (n: string) => { setNodeName(n); syncConfig(field, operator, value, n); };

  const conditionPreview = field ? `${field} ${operator} ${value || "?"}` : "not configured";

  return (
    <NodeWrapper id={id} name={nodeName} onNameChange={handleNameChange} accentColor="rose">
      <div className={`bg-[#1a1a2e] border rounded-xl shadow-2xl shadow-rose-500/5 w-72 overflow-hidden ${selected ? "border-rose-400 ring-1 ring-rose-400/30" : "border-rose-500/30"}`}>
        <div className="flex items-center gap-2 px-4 py-3 bg-rose-500/10 border-b border-rose-500/20">
          <GitBranch className="w-4 h-4 text-rose-400" />
          <span className="text-sm font-semibold text-rose-300">{nodeName}</span>
          <Badge variant="outline" className="ml-auto text-[10px] px-1.5 py-0 bg-rose-500/20 text-rose-400 border-rose-500/30 font-mono">
            {conditionPreview}
          </Badge>
        </div>
        <div className="p-4 space-y-3">
          <div>
            <div className="text-[10px] uppercase tracking-widest text-white/30 font-semibold mb-1.5">Field</div>
            <input
              value={field}
              onChange={(e) => handleFieldChange(e.target.value)}
              placeholder="e.g. age"
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-white/30 focus:outline-none focus:border-rose-500/50 font-mono"
            />
          </div>
          <div className="flex gap-2">
            <div className="flex-1">
              <div className="text-[10px] uppercase tracking-widest text-white/30 font-semibold mb-1.5">Operator</div>
              <select
                value={operator}
                onChange={(e) => handleOperatorChange(e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-rose-500/50"
              >
                {OPERATORS.map((op) => (
                  <option key={op} value={op} className="bg-[#1a1a2e]">{op}</option>
                ))}
              </select>
            </div>
            <div className="flex-1">
              <div className="text-[10px] uppercase tracking-widest text-white/30 font-semibold mb-1.5">Value</div>
              <input
                value={value}
                onChange={(e) => handleValueChange(e.target.value)}
                placeholder="e.g. 18"
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-white/30 focus:outline-none focus:border-rose-500/50 font-mono"
              />
            </div>
          </div>
          <div className="bg-white/5 rounded-lg px-3 py-2">
            <p className="text-[10px] text-white/40 leading-relaxed">
              Connect edges with <span className="text-rose-400 font-mono">condition: "true"</span> or <span className="text-rose-400 font-mono">"false"</span> to route data based on the result.
            </p>
          </div>
        </div>
        <Handle type="target" position={Position.Left} className="!bg-rose-500 !border-rose-300 !w-3 !h-3" />
        <Handle type="source" position={Position.Right} className="!bg-rose-500 !border-rose-300 !w-3 !h-3" />
      </div>
    </NodeWrapper>
  );
}
