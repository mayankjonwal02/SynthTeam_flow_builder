"use client";

import { Handle, Position, useReactFlow } from "reactflow";
import { useCallback, useState } from "react";
import { Cpu, Zap, Plus, Trash2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import NodeWrapper from "./NodeWrapper";
import FieldModeInput, { FieldMode } from "./FieldModeInput";

interface FieldMapping {
  name: string;
  source: FieldMode;
  value: string;
}

export default function ProcessorNode({ id, data, selected }: any) {
  const { setNodes } = useReactFlow();
  const [nodeName, setNodeName] = useState(data.label || "Processor");

  const [fields, setFields] = useState<FieldMapping[]>(() => {
    if (data.config?.field_mappings) return data.config.field_mappings;
    return [];
  });
  const [newFieldName, setNewFieldName] = useState("");

  const syncConfig = useCallback(
    (f: FieldMapping[], lbl?: string) => {
      setNodes((nds) =>
        nds.map((node) =>
          node.id === id
            ? {
                ...node,
                data: {
                  ...node.data,
                  label: lbl ?? node.data.label,
                  component: "echo_processor",
                  config: { ...node.data.config, label: lbl ?? node.data.label, field_mappings: f },
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
            ? { ...node, data: { ...node.data, component: "echo_processor", config: { ...node.data.config, label: nodeName, field_mappings: fields } } }
            : node
        )
      );
    });
  }

  const handleNameChange = (n: string) => { setNodeName(n); syncConfig(fields, n); };

  const addField = () => {
    if (!newFieldName.trim()) return;
    if (fields.some((f) => f.name === newFieldName.trim())) return;
    const updated: FieldMapping[] = [...fields, { name: newFieldName.trim(), source: "expression", value: `input.${newFieldName.trim()}` }];
    setFields(updated);
    syncConfig(updated);
    setNewFieldName("");
  };

  const removeField = (idx: number) => {
    const updated = fields.filter((_, i) => i !== idx);
    setFields(updated);
    syncConfig(updated);
  };

  const updateField = (idx: number, patch: Partial<FieldMapping>) => {
    const updated = fields.map((f, i) => (i === idx ? { ...f, ...patch } : f));
    setFields(updated);
    syncConfig(updated);
  };

  return (
    <NodeWrapper id={id} name={nodeName} onNameChange={handleNameChange} accentColor="amber">
    <div className={`bg-[#1a1a2e] border rounded-xl shadow-2xl shadow-amber-500/5 w-80 relative overflow-visible ${selected ? "border-amber-400 ring-1 ring-amber-400/30" : "border-amber-500/30"}`}>
      <div className="flex items-center gap-2 px-4 py-3 bg-amber-500/10 border-b border-amber-500/20">
        <Cpu className="w-4 h-4 text-amber-400" />
        <span className="text-sm font-semibold text-amber-300">{nodeName}</span>
        <Badge variant="outline" className="ml-auto text-[10px] px-1.5 py-0 bg-amber-500/20 text-amber-400 border-amber-500/30">
          <Zap className="w-2.5 h-2.5 mr-0.5" />
          {fields.length > 0 ? `${fields.length} mapped` : "Pass-through"}
        </Badge>
      </div>

      <div className="p-4 space-y-3">
        <div className="text-[10px] uppercase tracking-widest text-white/30 font-semibold">
          Field Mappings
        </div>

        {fields.map((f, i) => (
          <div key={i} className="bg-white/[0.03] border border-white/[0.06] rounded-lg p-2.5 space-y-2 group">
            <div className="flex items-center gap-2">
              <span className="text-xs text-white/80 font-mono font-medium flex-1">{f.name}</span>
              <button onClick={() => removeField(i)} className="opacity-0 group-hover:opacity-100 transition-opacity text-red-400 hover:text-red-300">
                <Trash2 className="w-3 h-3" />
              </button>
            </div>
            <FieldModeInput
              mode={f.source}
              value={f.value}
              onModeChange={(mode) => updateField(i, { source: mode, value: "" })}
              onValueChange={(value) => updateField(i, { value })}
              placeholder={{ static: "fixed value", input: "input.fieldName", expression: "input.data.items[0].name" }}
            />
          </div>
        ))}

        <div className="flex gap-1.5">
          <input
            value={newFieldName}
            onChange={(e) => setNewFieldName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && addField()}
            placeholder="field name"
            className="flex-1 bg-white/5 border border-white/10 rounded-md px-2 py-1 text-xs text-white placeholder-white/25 focus:outline-none focus:border-amber-500/50 font-mono"
          />
          <button onClick={addField} className="bg-amber-500/20 hover:bg-amber-500/30 text-amber-400 rounded-md px-2 transition-colors">
            <Plus className="w-3 h-3" />
          </button>
        </div>

        {fields.length === 0 && (
          <div className="bg-white/5 rounded-lg px-3 py-2">
            <p className="text-xs text-white/50 leading-relaxed">
              No mappings = pass-through. Add fields to transform data.
            </p>
          </div>
        )}
      </div>

      <Handle type="target" id="input" position={Position.Left} className="!bg-amber-500 !border-amber-300 !w-3 !h-3" title="Input" />
      <span className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-full pr-2 text-[9px] font-semibold uppercase tracking-wider text-white/50 whitespace-nowrap pointer-events-none">Input</span>
      <Handle type="source" id="output" position={Position.Right} className="!bg-amber-500 !border-amber-300 !w-3 !h-3" title="Output" />
      <span className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-full pl-2 text-[9px] font-semibold uppercase tracking-wider text-white/50 whitespace-nowrap pointer-events-none">Output</span>
    </div>
    </NodeWrapper>
  );
}
