"use client";

import { Handle, Position, useReactFlow } from "reactflow";
import { useCallback, useState } from "react";
import { Badge } from "@/components/ui/badge";
import NodeWrapper from "../NodeWrapper";
import FieldModeInput, { FieldMode } from "../FieldModeInput";

type AIFieldType =
  | "api_key" | "provider" | "model" | "temperature"
  | "system_prompt" | "prompt_template" | "tools"
  | "max_iterations" | "top_k" | "collection"
  | "schema" | "image_input" | "audio_input"
  | "goal" | "voice" | "text_template"
  | "agents_json" | "coordination_strategy"
  | "embedding_provider" | "vector_provider";

interface AINodeConfig {
  componentName: string;
  defaultLabel: string;
  accentColor: string;
  accentClasses: { border: string; bg: string; text: string; shadow: string };
  opBadge: string;
  icon: any;
  fields: AIFieldType[];
}

const PROVIDER_OPTIONS = ["openai", "anthropic", "gemini", "ollama", "groq", "mistral"];

const FIELD_META: Record<AIFieldType, { label: string; placeholder: string; type?: string; options?: string[] }> = {
  api_key:          { label: "API Key",        placeholder: "sk-...",              type: "password" },
  provider:         { label: "Provider",        placeholder: "openai",              options: PROVIDER_OPTIONS },
  model:            { label: "Model",           placeholder: "gpt-4o-mini" },
  temperature:      { label: "Temperature",     placeholder: "0.7",                 type: "number" },
  system_prompt:    { label: "System Prompt",    placeholder: "You are a helpful assistant..." },
  prompt_template:  { label: "Prompt Template",  placeholder: "{{input}}" },
  tools:            { label: "Tools",            placeholder: "web_search, calculator" },
  max_iterations:   { label: "Max Iterations",   placeholder: "10",                  type: "number" },
  top_k:            { label: "Top K",            placeholder: "5",                   type: "number" },
  collection:       { label: "Collection",       placeholder: "my_collection" },
  schema:           { label: "Output Schema (JSON)", placeholder: '{"type":"object",...}' },
  image_input:      { label: "Image URL / Base64", placeholder: "https://... or base64" },
  audio_input:      { label: "Audio Path",       placeholder: "/path/to/audio.wav" },
  goal:             { label: "Goal",             placeholder: "Describe the high-level goal..." },
  voice:            { label: "Voice",            placeholder: "alloy" },
  text_template:    { label: "Text Template",    placeholder: "{{input.text}}" },
  agents_json:      { label: "Agents Config (JSON)", placeholder: '[{"id":"researcher","tools":["web_search"]}]' },
  coordination_strategy: { label: "Strategy", placeholder: "sequential", options: ["sequential", "collaborative"] },
  embedding_provider: { label: "Embedding Provider", placeholder: "openai", options: ["openai", "ollama", "huggingface"] },
  vector_provider:  { label: "Vector Store",     placeholder: "chroma",             options: ["chroma", "qdrant", "pinecone", "weaviate", "supabase"] },
};

export function createAINode(cfg: AINodeConfig) {
  return function AINodeInstance({ id, data, selected }: any) {
    const { setNodes } = useReactFlow();
    const [nodeName, setNodeName] = useState(data.label || cfg.defaultLabel);
    const [values, setValues] = useState<Record<string, string>>(() => {
      const init: Record<string, string> = {};
      cfg.fields.forEach(f => { init[f] = data.config?.[f] || ""; });
      return init;
    });

    const syncConfig = useCallback(
      (vals: Record<string, string>, lbl?: string) => {
        const config: any = { ...vals };
        setNodes((nds) =>
          nds.map((n) =>
            n.id === id
              ? { ...n, data: { ...n.data, label: lbl ?? n.data.label, component: cfg.componentName, config } }
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

    const updateField = (field: string, value: string) => {
      const updated = { ...values, [field]: value };
      setValues(updated);
      syncConfig(updated);
    };

    const Icon = cfg.icon;
    const ac = cfg.accentClasses;

    return (
      <NodeWrapper id={id} name={nodeName} onNameChange={(n) => { setNodeName(n); syncConfig(values, n); }} accentColor={cfg.accentColor}>
        <div className={`bg-[#1a1a2e] border rounded-xl shadow-2xl ${ac.shadow} w-80 relative overflow-visible ${selected ? `${ac.border} ring-1 ring-${cfg.accentColor}-400/30` : ac.border.replace("400", "500/30")}`}>
          <div className={`flex items-center gap-2 px-4 py-3 ${ac.bg} border-b ${ac.border.replace("400", "500/20")}`}>
            <Icon className={`w-4 h-4 ${ac.text}`} />
            <span className={`text-sm font-semibold ${ac.text.replace("400", "300")}`}>{nodeName}</span>
            <Badge variant="outline" className={`ml-auto text-[10px] px-1.5 py-0 ${ac.bg} ${ac.text} ${ac.border}`}>{cfg.opBadge}</Badge>
          </div>
          <div className="p-4 space-y-2.5">
            {cfg.fields.map((field) => {
              const meta = FIELD_META[field];
              return (
                <div key={field}>
                  <div className="text-[10px] uppercase tracking-widest text-white/30 font-semibold mb-1">{meta.label}</div>
                  {meta.options ? (
                    <select
                      value={values[field] || meta.options[0]}
                      onChange={(e) => updateField(field, e.target.value)}
                      className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none"
                    >
                      {meta.options.map(o => (
                        <option key={o} value={o} className="bg-[#1a1a2e]">{o}</option>
                      ))}
                    </select>
                  ) : field === "system_prompt" || field === "prompt_template" || field === "schema" || field === "agents_json" || field === "goal" ? (
                    <textarea
                      value={values[field]}
                      onChange={(e) => updateField(field, e.target.value)}
                      rows={3}
                      spellCheck={false}
                      placeholder={meta.placeholder}
                      className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white placeholder-white/20 focus:outline-none font-mono resize-y"
                    />
                  ) : (
                    <input
                      type={meta.type || "text"}
                      value={values[field]}
                      onChange={(e) => updateField(field, e.target.value)}
                      placeholder={meta.placeholder}
                      className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white placeholder-white/25 focus:outline-none font-mono"
                    />
                  )}
                </div>
              );
            })}
          </div>
          <Handle type="target" id="input" position={Position.Left} className={`!w-3 !h-3 !bg-${cfg.accentColor}-500 !border-${cfg.accentColor}-300`} title="Input" />
          <span className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-full pr-2 text-[9px] font-semibold uppercase tracking-wider text-white/50 whitespace-nowrap pointer-events-none">Input</span>
          <Handle type="source" id="output" position={Position.Right} className={`!w-3 !h-3 !bg-${cfg.accentColor}-500 !border-${cfg.accentColor}-300`} title="Output" />
          <span className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-full pl-2 text-[9px] font-semibold uppercase tracking-wider text-white/50 whitespace-nowrap pointer-events-none">Output</span>
        </div>
      </NodeWrapper>
    );
  };
}
