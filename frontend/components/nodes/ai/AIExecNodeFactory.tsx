"use client";

import { Handle, Position, useReactFlow } from "reactflow";
import { useCallback, useState } from "react";
import { Badge } from "@/components/ui/badge";
import NodeWrapper from "../NodeWrapper";
import FieldModeInput, { type FieldMode } from "../FieldModeInput";

type HandleDef = {
  id: string;
  label: string;
  color: string;
};

interface ExecField {
  key: string;
  label: string;
  placeholder: string;
  type?: "text" | "textarea";
  /** When set, this field uses Static/Input/Expr mode; mode stored in config[sourceKey]. */
  sourceKey?: string;
  placeholderMode?: { static?: string; input?: string; expression?: string };
}

interface AIExecNodeConfig {
  componentName: string;
  defaultLabel: string;
  accentColor: string;
  accentClasses: { border: string; bg: string; text: string; shadow: string };
  badge: string;
  icon: any;
  targetHandles: HandleDef[];
  fields: ExecField[];
}

export function createAIExecNode(cfg: AIExecNodeConfig) {
  return function AIExecNodeInstance({ id, data, selected }: any) {
    const { setNodes } = useReactFlow();
    const [nodeName, setNodeName] = useState(data.label || cfg.defaultLabel);
    const [values, setValues] = useState<Record<string, string>>(() => {
      const init: Record<string, string> = {};
      cfg.fields.forEach(f => {
        init[f.key] = data.config?.[f.key] ?? "";
        if (f.sourceKey) init[f.sourceKey] = data.config?.[f.sourceKey] ?? "static";
      });
      return init;
    });

    const syncConfig = useCallback(
      (vals: Record<string, string>, lbl?: string) => {
        setNodes((nds) =>
          nds.map((n) =>
            n.id === id
              ? { ...n, data: { ...n.data, label: lbl ?? n.data.label, component: cfg.componentName, config: { ...vals } } }
              : n
          )
        );
      },
      [id, setNodes]
    );

    if (!data.component) {
      queueMicrotask(() => {
        setNodes((nds) =>
          nds.map((n) =>
            n.id === id ? { ...n, data: { ...n.data, component: cfg.componentName } } : n
          )
        );
      });
    }

    const updateField = (key: string, value: string) => {
      const updated = { ...values, [key]: value };
      setValues(updated);
      syncConfig(updated);
    };

    const updateModeField = (valueKey: string, sourceKey: string, mode: FieldMode, value: string) => {
      const updated = { ...values, [sourceKey]: mode, [valueKey]: value };
      setValues(updated);
      syncConfig(updated);
    };

    const Icon = cfg.icon;
    const ac = cfg.accentClasses;
    const handleCount = cfg.targetHandles.length;
    const handleSpacing = 100 / (handleCount + 1);

    return (
      <NodeWrapper id={id} name={nodeName} onNameChange={(n) => { setNodeName(n); syncConfig(values, n); }} accentColor={cfg.accentColor}>
        <div className={`bg-[#1a1a2e] border rounded-xl shadow-2xl ${ac.shadow} w-80 overflow-visible relative ${selected ? `${ac.border} ring-1 ring-${cfg.accentColor}-400/30` : ac.border.replace("400", "500/30")}`}>
          {/* Data input handle at edge + label as sibling */}
          <Handle
            type="target"
            id="input"
            position={Position.Left}
            className={`!w-3 !h-3 !bg-${cfg.accentColor}-500 !border-${cfg.accentColor}-300`}
            title="Input"
          />
          <span className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-full pr-2 text-[9px] font-semibold uppercase tracking-wider text-white/50 whitespace-nowrap pointer-events-none">Input</span>

          {/* Typed target handles on top */}
          {cfg.targetHandles.map((h, i) => (
            <div key={h.id}>
              <Handle
                type="target"
                position={Position.Top}
                id={h.id}
                style={{ left: `${handleSpacing * (i + 1)}%` }}
                className={`!w-3 !h-3 !border-2 !rounded-full`}
                title={h.label}
              />
              <div
                className="absolute text-[7px] font-bold uppercase tracking-wider text-white/40 whitespace-nowrap pointer-events-none"
                style={{ left: `${handleSpacing * (i + 1)}%`, top: -18, transform: "translateX(-50%)" }}
              >
                {h.label}
              </div>
            </div>
          ))}

          {/* Header */}
          <div className={`flex items-center gap-2 px-4 py-3 ${ac.bg} border-b ${ac.border.replace("400", "500/20")}`}>
            <Icon className={`w-4 h-4 ${ac.text}`} />
            <span className={`text-sm font-semibold ${ac.text.replace("400", "300")}`}>{nodeName}</span>
            <Badge variant="outline" className={`ml-auto text-[10px] px-1.5 py-0 ${ac.bg} ${ac.text} ${ac.border}`}>{cfg.badge}</Badge>
          </div>

          {/* Connected handles indicator */}
          <div className="px-4 pt-2 flex flex-wrap gap-1">
            {cfg.targetHandles.map((h) => (
              <span key={h.id} className="text-[8px] uppercase tracking-wider bg-white/5 border border-white/10 rounded px-1.5 py-0.5 text-white/30">
                {h.label}
              </span>
            ))}
          </div>

          {/* Node-specific fields */}
          {cfg.fields.length > 0 && (
            <div className="p-4 pt-2 space-y-2.5">
              {cfg.fields.map((field) => (
                <div key={field.key}>
                  <div className="text-[10px] uppercase tracking-widest text-white/30 font-semibold mb-1">{field.label}</div>
                  {field.sourceKey ? (
                    <FieldModeInput
                      mode={(values[field.sourceKey] as FieldMode) || "static"}
                      value={values[field.key] ?? ""}
                      onModeChange={(mode) => updateModeField(field.key, field.sourceKey!, mode, values[field.key] ?? "")}
                      onValueChange={(value) => updateModeField(field.key, field.sourceKey!, (values[field.sourceKey!] as FieldMode) || "static", value)}
                      placeholder={field.placeholderMode ?? { static: field.placeholder, input: "input", expression: "input.data.x" }}
                    />
                  ) : field.type === "textarea" ? (
                    <textarea
                      value={values[field.key]}
                      onChange={(e) => updateField(field.key, e.target.value)}
                      rows={3}
                      spellCheck={false}
                      placeholder={field.placeholder}
                      className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white placeholder-white/20 focus:outline-none font-mono resize-y"
                    />
                  ) : (
                    <input
                      type="text"
                      value={values[field.key]}
                      onChange={(e) => updateField(field.key, e.target.value)}
                      placeholder={field.placeholder}
                      className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white placeholder-white/25 focus:outline-none font-mono"
                    />
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Data output handle at edge + label as sibling */}
          <Handle
            type="source"
            id="output"
            position={Position.Right}
            className={`!w-3 !h-3 !bg-${cfg.accentColor}-500 !border-${cfg.accentColor}-300`}
            title="Output"
          />
          <span className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-full pl-2 text-[9px] font-semibold uppercase tracking-wider text-white/50 whitespace-nowrap pointer-events-none">Output</span>
        </div>
      </NodeWrapper>
    );
  };
}
