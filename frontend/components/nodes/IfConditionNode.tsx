"use client";

import { Handle, Position, useReactFlow } from "reactflow";
import { useCallback, useState } from "react";
import { GitBranch } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import NodeWrapper from "./NodeWrapper";
import FieldModeInput, { FieldMode } from "./FieldModeInput";

const OPERATORS = ["==", "!=", ">", "<", ">=", "<="] as const;

interface ModeValue { mode: FieldMode; value: string; }

export default function IfConditionNode({ id, data, selected }: any) {
  const { setNodes } = useReactFlow();
  const [nodeName, setNodeName] = useState(data.label || "If Condition");
  const [field, setField] = useState<ModeValue>({
    mode: data.config?.field_mode || "expression",
    value: data.config?.field || "",
  });
  const [operator, setOperator] = useState<string>(data.config?.operator || "==");
  const [compareValue, setCompareValue] = useState<ModeValue>({
    mode: data.config?.value_mode || "static",
    value: String(data.config?.value ?? ""),
  });

  const syncConfig = useCallback(
    (f: ModeValue, op: string, v: ModeValue, lbl?: string) => {
      setNodes((nds) =>
        nds.map((node) =>
          node.id === id
            ? {
                ...node,
                data: {
                  ...node.data,
                  label: lbl ?? node.data.label,
                  component: "if_condition",
                  config: {
                    ...node.data.config,
                    field: f.value,
                    field_mode: f.mode,
                    operator: op,
                    value: v.value,
                    value_mode: v.mode,
                  },
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
            ? { ...node, data: { ...node.data, component: "if_condition", config: { ...node.data.config, field: field.value, field_mode: field.mode, operator, value: compareValue.value, value_mode: compareValue.mode } } }
            : node
        )
      );
    });
  }

  const handleNameChange = (n: string) => { setNodeName(n); syncConfig(field, operator, compareValue, n); };

  const conditionPreview = field.value ? `${field.value} ${operator} ${compareValue.value || "?"}` : "not configured";

  return (
    <NodeWrapper id={id} name={nodeName} onNameChange={handleNameChange} accentColor="rose">
      <div className={`bg-[#1a1a2e] border rounded-xl shadow-2xl shadow-rose-500/5 w-80 overflow-hidden ${selected ? "border-rose-400 ring-1 ring-rose-400/30" : "border-rose-500/30"}`}>
        <div className="flex items-center gap-2 px-4 py-3 bg-rose-500/10 border-b border-rose-500/20">
          <GitBranch className="w-4 h-4 text-rose-400" />
          <span className="text-sm font-semibold text-rose-300">{nodeName}</span>
          <Badge variant="outline" className="ml-auto text-[10px] px-1.5 py-0 bg-rose-500/20 text-rose-400 border-rose-500/30 font-mono truncate max-w-[120px]">
            {conditionPreview}
          </Badge>
        </div>
        <div className="p-4 space-y-3">
          <div>
            <div className="text-[10px] uppercase tracking-widest text-white/30 font-semibold mb-1.5">Field</div>
            <FieldModeInput
              mode={field.mode}
              value={field.value}
              onModeChange={(mode) => { const u = { mode, value: "" }; setField(u); syncConfig(u, operator, compareValue); }}
              onValueChange={(value) => { const u = { ...field, value }; setField(u); syncConfig(u, operator, compareValue); }}
              placeholder={{ static: "age", input: "input.age", expression: "input.user.age" }}
            />
          </div>
          <div className="flex gap-2">
            <div className="flex-1">
              <div className="text-[10px] uppercase tracking-widest text-white/30 font-semibold mb-1.5">Operator</div>
              <select
                value={operator}
                onChange={(e) => { setOperator(e.target.value); syncConfig(field, e.target.value, compareValue); }}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-rose-500/50"
              >
                {OPERATORS.map((op) => (
                  <option key={op} value={op} className="bg-[#1a1a2e]">{op}</option>
                ))}
              </select>
            </div>
          </div>
          <div>
            <div className="text-[10px] uppercase tracking-widest text-white/30 font-semibold mb-1.5">Compare Value</div>
            <FieldModeInput
              mode={compareValue.mode}
              value={compareValue.value}
              onModeChange={(mode) => { const u = { mode, value: "" }; setCompareValue(u); syncConfig(field, operator, u); }}
              onValueChange={(value) => { const u = { ...compareValue, value }; setCompareValue(u); syncConfig(field, operator, u); }}
              placeholder={{ static: "18", input: "input.threshold", expression: "input.config.minAge" }}
            />
          </div>
          <div className="bg-white/5 rounded-lg px-3 py-2">
            <p className="text-[10px] text-white/40 leading-relaxed">
              Routes data to <span className="text-rose-400 font-mono">true</span> or <span className="text-rose-400 font-mono">false</span> branch based on the condition.
            </p>
          </div>
        </div>
        <Handle type="target" position={Position.Left} className="!bg-rose-500 !border-rose-300 !w-3 !h-3" />
        <Handle type="source" position={Position.Right} className="!bg-rose-500 !border-rose-300 !w-3 !h-3" />
      </div>
    </NodeWrapper>
  );
}
