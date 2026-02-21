"use client";

import { Handle, Position, useReactFlow } from "reactflow";
import { useCallback, useState } from "react";
import { Send, Plus, Trash2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import NodeWrapper from "./NodeWrapper";
import FieldModeInput, { FieldMode } from "./FieldModeInput";

const FIELD_TYPES = [
  "any",
  "string", "int", "float", "bool",
  "list", "dict", "json",
  "base64", "bytes",
  "image", "audio", "video", "file",
  "date", "datetime",
  "url", "email", "uuid",
] as const;

interface FieldMapping {
  name: string;
  type: string;
  source: FieldMode;  // "input" | "static" | "expression"
  value: string;      // for input: key; for static: literal; for expression: expression string
}

export default function ResponseNode({ id, data, selected }: any) {
  const { setNodes } = useReactFlow();
  const [nodeName, setNodeName] = useState(data.label || "Response");

  const [fields, setFields] = useState<FieldMapping[]>(() => {
    // Restore from saved config
    if (data.config?.field_mappings) {
      return data.config.field_mappings;
    }
    // Backward compat: old-style response_schema → convert to field_mappings
    const schema = data.config?.response_schema || {};
    return Object.entries(schema).map(([k, v]) => ({
      name: k,
      type: v as string,
      source: "input" as const,
      value: k,
    }));
  });

  const [newFieldName, setNewFieldName] = useState("");
  const [newFieldType, setNewFieldType] = useState("any");

  // ── immutable state update via setNodes ──
  const syncConfig = useCallback(
    (f: FieldMapping[], lbl?: string) => {
      const schema: Record<string, string> = {};
      f.forEach((field) => (schema[field.name] = field.type));

      setNodes((nds) =>
        nds.map((node) =>
          node.id === id
            ? {
                ...node,
                data: {
                  ...node.data,
                  label: lbl ?? node.data.label,
                  component: "response_builder",
                  config: {
                    is_response: true,
                    response_schema: schema,
                    field_mappings: f,
                  },
                },
              }
            : node
        )
      );
    },
    [id, setNodes]
  );

  const handleNameChange = (n: string) => {
    setNodeName(n);
    syncConfig(fields, n);
  };

  // Ensure component is set on first render
  if (!data.component) {
    // Use a microtask to avoid updating state during render
    queueMicrotask(() => {
      setNodes((nds) =>
        nds.map((node) =>
          node.id === id
            ? {
                ...node,
                data: {
                  ...node.data,
                  component: "response_builder",
                  config: { ...node.data.config, is_response: true },
                },
              }
            : node
        )
      );
    });
  }

  // ── add / remove / update fields ──
  const addField = () => {
    if (!newFieldName.trim()) return;
    if (fields.some((f) => f.name === newFieldName.trim())) return;
    const updated: FieldMapping[] = [
      ...fields,
      { name: newFieldName.trim(), type: newFieldType, source: "input", value: newFieldName.trim() },
    ];
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
    <NodeWrapper id={id} name={nodeName} onNameChange={handleNameChange} accentColor="emerald">
    <div className={`bg-[#1a1a2e] border rounded-xl shadow-2xl shadow-emerald-500/5 w-[310px] relative overflow-visible ${selected ? "border-emerald-400 ring-1 ring-emerald-400/30" : "border-emerald-500/30"}`}>
      {/* ── header ── */}
      <div className="flex items-center gap-2 px-4 py-3 bg-emerald-500/10 border-b border-emerald-500/20">
        <Send className="w-4 h-4 text-emerald-400" />
        <span className="text-sm font-semibold text-emerald-300">{nodeName}</span>
        <Badge
          variant="outline"
          className="ml-auto text-[10px] px-1.5 py-0 bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
        >
          {fields.length} field{fields.length !== 1 ? "s" : ""}
        </Badge>
      </div>

      <div className="p-4 space-y-3">
        <div className="text-[10px] uppercase tracking-widest text-white/30 font-semibold">
          Field Mappings
        </div>

        {/* ── existing fields ── */}
        {fields.map((f, i) => (
          <div
            key={i}
            className="bg-white/[0.03] border border-white/[0.06] rounded-lg p-2.5 space-y-2 group"
          >
            {/* row 1: name + type + delete */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-white/80 font-mono font-medium flex-1">
                {f.name}
              </span>
              <Badge variant="outline" className="text-[9px] bg-white/5 text-white/40 border-white/10">
                {f.type}
              </Badge>
              <button
                onClick={() => removeField(i)}
                className="opacity-0 group-hover:opacity-100 transition-opacity text-red-400 hover:text-red-300"
              >
                <Trash2 className="w-3 h-3" />
              </button>
            </div>

            {/* row 2: source toggle + value */}
            <FieldModeInput
              mode={f.source}
              value={f.value}
              onModeChange={(mode) => updateField(i, { source: mode, value: "" })}
              onValueChange={(value) => updateField(i, { value })}
              placeholder={{
                static: "fixed value",
                input: "input.fieldName",
                expression: "input.data.items[0].name",
              }}
            />
          </div>
        ))}

        {/* ── add field row ── */}
        <div className="flex gap-1.5">
          <input
            value={newFieldName}
            onChange={(e) => setNewFieldName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && addField()}
            placeholder="field name"
            className="flex-1 bg-white/5 border border-white/10 rounded-md px-2 py-1 text-xs text-white placeholder-white/25 focus:outline-none focus:border-emerald-500/50 font-mono"
          />
          <select
            value={newFieldType}
            onChange={(e) => setNewFieldType(e.target.value)}
            className="bg-white/5 border border-white/10 rounded-md px-1.5 text-xs text-white/70 focus:outline-none"
          >
            {FIELD_TYPES.map((t) => (
              <option key={t} value={t} className="bg-[#1a1a2e]">
                {t}
              </option>
            ))}
          </select>
          <button
            onClick={addField}
            className="bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 rounded-md px-2 transition-colors"
          >
            <Plus className="w-3 h-3" />
          </button>
        </div>

        {fields.length === 0 && (
          <p className="text-[11px] text-white/20 text-center py-2">
            Add fields to define the response shape.
            <br />
            Each field maps to upstream data or a static value.
          </p>
        )}
      </div>

      <Handle
        type="target"
        id="input"
        position={Position.Left}
        className="!bg-emerald-500 !border-emerald-300 !w-3 !h-3"
        title="Input"
      />
      <span className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-full pr-2 text-[9px] font-semibold uppercase tracking-wider text-white/50 whitespace-nowrap pointer-events-none">Input</span>
    </div>
    </NodeWrapper>
  );
}
