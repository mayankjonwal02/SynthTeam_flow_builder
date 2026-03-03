"use client";

import { Handle, Position, useReactFlow } from "reactflow";
import { useCallback, useState } from "react";
import { Badge } from "@/components/ui/badge";
import NodeWrapper from "../NodeWrapper";

interface ConfigField {
  key: string;
  label: string;
  placeholder: string;
  type?: "text" | "password" | "number" | "select" | "textarea";
  options?: string[];
}

interface ConfigNodeConfig {
  componentName: string;
  defaultLabel: string;
  accentColor: string;
  accentClasses: { border: string; bg: string; text: string; shadow: string };
  handleType: string;
  handleLabel: string;
  badge: string;
  icon: any;
  fields: ConfigField[];
}

export function createConfigNode(cfg: ConfigNodeConfig) {
  return function ConfigNodeInstance({ id, data, selected }: any) {
    const { setNodes } = useReactFlow();
    const [nodeName, setNodeName] = useState(data.label || cfg.defaultLabel);
    const [values, setValues] = useState<Record<string, string>>(() => {
      const init: Record<string, string> = {};
      cfg.fields.forEach(f => { init[f.key] = data.config?.[f.key] || ""; });
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

    const Icon = cfg.icon;
    const ac = cfg.accentClasses;

    return (
      <NodeWrapper id={id} name={nodeName} onNameChange={(n) => { setNodeName(n); syncConfig(values, n); }} accentColor={cfg.accentColor}>
        <div className={`bg-[#1a1a2e] border rounded-xl shadow-lg ${ac.shadow} w-64 overflow-hidden relative ${selected ? `${ac.border} ring-1 ring-${cfg.accentColor}-400/30` : ac.border.replace("400", "500/30")}`}>
          {/* Data input handle at edge + label as sibling */}
          <Handle
            type="target"
            id="input"
            position={Position.Left}
            className="!w-2.5 !h-2.5 !bg-white/20 !border-white/30"
            title="Input"
          />
          <span className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-full pr-2 text-[9px] font-semibold uppercase tracking-wider text-white/50 whitespace-nowrap pointer-events-none">Input</span>
          <div className={`flex items-center gap-2 px-3 py-2 ${ac.bg} border-b ${ac.border.replace("400", "500/20")}`}>
            <Icon className={`w-3.5 h-3.5 ${ac.text}`} />
            <span className={`text-xs font-semibold ${ac.text.replace("400", "300")}`}>{nodeName}</span>
            <Badge variant="outline" className={`ml-auto text-[9px] px-1.5 py-0 ${ac.bg} ${ac.text} ${ac.border}`}>{cfg.badge}</Badge>
          </div>
          <div className="p-3 space-y-2">
            {cfg.fields.map((field) => (
              <div key={field.key}>
                <div className="text-[9px] uppercase tracking-widest text-white/30 font-semibold mb-0.5">{field.label}</div>
                {field.type === "select" && field.options ? (
                  <select
                    value={values[field.key] || field.options[0]}
                    onChange={(e) => updateField(field.key, e.target.value)}
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-2 py-1 text-[11px] text-white focus:outline-none"
                  >
                    {field.options.map(o => (
                      <option key={o} value={o} className="bg-[#1a1a2e]">{o}</option>
                    ))}
                  </select>
                ) : field.type === "textarea" ? (
                  <textarea
                    value={values[field.key]}
                    onChange={(e) => updateField(field.key, e.target.value)}
                    rows={3}
                    spellCheck={false}
                    placeholder={field.placeholder}
                    className="w-full bg-black/40 border border-white/10 rounded-lg px-2 py-1 text-[11px] text-white placeholder-white/20 focus:outline-none font-mono resize-y"
                  />
                ) : (
                  <input
                    type={field.type || "text"}
                    value={values[field.key]}
                    onChange={(e) => updateField(field.key, e.target.value)}
                    placeholder={field.placeholder}
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-2 py-1 text-[11px] text-white placeholder-white/25 focus:outline-none font-mono"
                  />
                )}
              </div>
            ))}
          </div>
          {/* Typed source handle at edge + label as sibling */}
          <Handle
            type="source"
            position={Position.Right}
            id={cfg.handleType}
            className={`!w-3 !h-3 !bg-${cfg.accentColor}-500 !border-${cfg.accentColor}-300`}
            title={cfg.handleLabel}
          />
          <span className={`absolute right-0 top-1/2 -translate-y-1/2 translate-x-full pl-2 text-[9px] font-semibold uppercase tracking-wider ${ac.text} opacity-70 whitespace-nowrap pointer-events-none`}>{cfg.handleLabel}</span>
        </div>
      </NodeWrapper>
    );
  };
}
