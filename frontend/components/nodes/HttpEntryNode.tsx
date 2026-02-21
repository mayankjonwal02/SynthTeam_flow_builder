"use client";

import { Handle, Position, useReactFlow } from "reactflow";
import { useCallback, useState } from "react";
import { Globe, Plus, Trash2, ArrowDownToLine, ArrowUpFromLine } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import NodeWrapper from "./NodeWrapper";

const METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH"] as const;
const FIELD_TYPES = [
  "any",
  "string", "int", "float", "bool",
  "list", "dict", "json",
  "base64", "bytes",
  "image", "audio", "video", "file",
  "date", "datetime",
  "url", "email", "uuid",
] as const;

const METHOD_COLORS: Record<string, string> = {
  GET:    "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  POST:   "bg-blue-500/20 text-blue-400 border-blue-500/30",
  PUT:    "bg-amber-500/20 text-amber-400 border-amber-500/30",
  DELETE: "bg-red-500/20 text-red-400 border-red-500/30",
  PATCH:  "bg-purple-500/20 text-purple-400 border-purple-500/30",
};

interface SchemaField {
  name: string;
  type: string;
}

export default function HttpEntryNode({ id, data, selected }: any) {
  const { setNodes } = useReactFlow();

  const [nodeName, setNodeName] = useState(data.label || "HTTP Entry");
  const [method, setMethod] = useState<string>(data.config?.method || "POST");
  const [path, setPath] = useState<string>(data.config?.path || "/api/endpoint");

  // Request schema fields
  const [reqFields, setReqFields] = useState<SchemaField[]>(() => {
    const schema = data.config?.request_schema || {};
    return Object.entries(schema).map(([k, v]) => ({ name: k, type: v as string }));
  });
  const [newReqName, setNewReqName] = useState("");
  const [newReqType, setNewReqType] = useState("any");

  // Response schema fields
  const [resFields, setResFields] = useState<SchemaField[]>(() => {
    const schema = data.config?.response_schema || {};
    return Object.entries(schema).map(([k, v]) => ({ name: k, type: v as string }));
  });
  const [newResName, setNewResName] = useState("");
  const [newResType, setNewResType] = useState("any");

  // ── immutable state update via setNodes ──
  const syncConfig = useCallback(
    (m: string, p: string, req: SchemaField[], res: SchemaField[], lbl?: string) => {
      const reqSchema: Record<string, string> = {};
      req.forEach((f) => (reqSchema[f.name] = f.type));
      const resSchema: Record<string, string> = {};
      res.forEach((f) => (resSchema[f.name] = f.type));

      setNodes((nds) =>
        nds.map((node) =>
          node.id === id
            ? {
                ...node,
                data: {
                  ...node.data,
                  label: lbl ?? node.data.label,
                  component: "http_entry",
                  config: {
                    is_entry: true,
                    method: m,
                    path: p,
                    request_schema: reqSchema,
                    response_schema: resSchema,
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
    syncConfig(method, path, reqFields, resFields, n);
  };

  const handleMethodChange = (m: string) => {
    setMethod(m);
    syncConfig(m, path, reqFields, resFields);
  };

  const handlePathChange = (p: string) => {
    setPath(p);
    syncConfig(method, p, reqFields, resFields);
  };

  // ── request schema helpers ──
  const addReqField = () => {
    if (!newReqName.trim()) return;
    if (reqFields.some((f) => f.name === newReqName.trim())) return;
    const updated = [...reqFields, { name: newReqName.trim(), type: newReqType }];
    setReqFields(updated);
    syncConfig(method, path, updated, resFields);
    setNewReqName("");
  };
  const removeReqField = (idx: number) => {
    const updated = reqFields.filter((_, i) => i !== idx);
    setReqFields(updated);
    syncConfig(method, path, updated, resFields);
  };

  // ── response schema helpers ──
  const addResField = () => {
    if (!newResName.trim()) return;
    if (resFields.some((f) => f.name === newResName.trim())) return;
    const updated = [...resFields, { name: newResName.trim(), type: newResType }];
    setResFields(updated);
    syncConfig(method, path, reqFields, updated);
    setNewResName("");
  };
  const removeResField = (idx: number) => {
    const updated = resFields.filter((_, i) => i !== idx);
    setResFields(updated);
    syncConfig(method, path, reqFields, updated);
  };

  return (
    <NodeWrapper id={id} name={nodeName} onNameChange={handleNameChange} accentColor="blue">
    <div className={`bg-[#1a1a2e] border rounded-xl shadow-2xl shadow-blue-500/5 w-[310px] relative overflow-visible ${selected ? "border-blue-400 ring-1 ring-blue-400/30" : "border-blue-500/30"}`}>
      {/* ── header ── */}
      <div className="flex items-center gap-2 px-4 py-3 bg-blue-500/10 border-b border-blue-500/20">
        <Globe className="w-4 h-4 text-blue-400" />
        <span className="text-sm font-semibold text-blue-300">{nodeName}</span>
        <Badge
          variant="outline"
          className={`ml-auto text-[10px] px-1.5 py-0 ${METHOD_COLORS[method] || ""}`}
        >
          {method}
        </Badge>
      </div>

      <div className="p-4 space-y-3">
        {/* ── method selector ── */}
        <div className="flex gap-1">
          {METHODS.map((m) => (
            <button
              key={m}
              onClick={() => handleMethodChange(m)}
              className={`flex-1 text-[10px] font-bold py-1 rounded-md transition-all ${
                method === m
                  ? METHOD_COLORS[m] + " border"
                  : "bg-white/5 text-white/40 hover:bg-white/10"
              }`}
            >
              {m}
            </button>
          ))}
        </div>

        {/* ── path input ── */}
        <input
          value={path}
          onChange={(e) => handlePathChange(e.target.value)}
          placeholder="/api/endpoint"
          className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-white/30 focus:outline-none focus:border-blue-500/50 font-mono"
        />

        {/* ── request schema ── */}
        <div className="space-y-2">
          <div className="flex items-center gap-1.5">
            <ArrowDownToLine className="w-3 h-3 text-blue-400/60" />
            <span className="text-[10px] uppercase tracking-widest text-white/30 font-semibold">
              Request Schema
            </span>
            <Badge variant="outline" className="ml-auto text-[9px] px-1 py-0 bg-blue-500/10 text-blue-400/60 border-blue-500/20">
              {reqFields.length}
            </Badge>
          </div>

          {reqFields.map((f, i) => (
            <div
              key={i}
              className="flex items-center gap-2 bg-white/5 rounded-lg px-3 py-1.5 group"
            >
              <span className="text-xs text-white/80 flex-1 font-mono">{f.name}</span>
              <Badge variant="outline" className="text-[10px] bg-white/5 text-white/50 border-white/10">
                {f.type}
              </Badge>
              <button
                onClick={() => removeReqField(i)}
                className="opacity-0 group-hover:opacity-100 transition-opacity text-red-400 hover:text-red-300"
              >
                <Trash2 className="w-3 h-3" />
              </button>
            </div>
          ))}

          <div className="flex gap-1.5">
            <input
              value={newReqName}
              onChange={(e) => setNewReqName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && addReqField()}
              placeholder="field name"
              className="flex-1 bg-white/5 border border-white/10 rounded-md px-2 py-1 text-xs text-white placeholder-white/25 focus:outline-none focus:border-blue-500/50 font-mono"
            />
            <select
              value={newReqType}
              onChange={(e) => setNewReqType(e.target.value)}
              className="bg-white/5 border border-white/10 rounded-md px-1.5 text-xs text-white/70 focus:outline-none"
            >
              {FIELD_TYPES.map((t) => (
                <option key={t} value={t} className="bg-[#1a1a2e]">{t}</option>
              ))}
            </select>
            <button
              onClick={addReqField}
              className="bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 rounded-md px-2 transition-colors"
            >
              <Plus className="w-3 h-3" />
            </button>
          </div>
        </div>

        {/* ── divider ── */}
        <div className="border-t border-white/[0.06]" />

        {/* ── response schema ── */}
        <div className="space-y-2">
          <div className="flex items-center gap-1.5">
            <ArrowUpFromLine className="w-3 h-3 text-emerald-400/60" />
            <span className="text-[10px] uppercase tracking-widest text-white/30 font-semibold">
              Response Schema
            </span>
            <Badge variant="outline" className="ml-auto text-[9px] px-1 py-0 bg-emerald-500/10 text-emerald-400/60 border-emerald-500/20">
              {resFields.length}
            </Badge>
          </div>

          {resFields.map((f, i) => (
            <div
              key={i}
              className="flex items-center gap-2 bg-white/5 rounded-lg px-3 py-1.5 group"
            >
              <span className="text-xs text-white/80 flex-1 font-mono">{f.name}</span>
              <Badge variant="outline" className="text-[10px] bg-white/5 text-white/50 border-white/10">
                {f.type}
              </Badge>
              <button
                onClick={() => removeResField(i)}
                className="opacity-0 group-hover:opacity-100 transition-opacity text-red-400 hover:text-red-300"
              >
                <Trash2 className="w-3 h-3" />
              </button>
            </div>
          ))}

          <div className="flex gap-1.5">
            <input
              value={newResName}
              onChange={(e) => setNewResName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && addResField()}
              placeholder="field name"
              className="flex-1 bg-white/5 border border-white/10 rounded-md px-2 py-1 text-xs text-white placeholder-white/25 focus:outline-none focus:border-emerald-500/50 font-mono"
            />
            <select
              value={newResType}
              onChange={(e) => setNewResType(e.target.value)}
              className="bg-white/5 border border-white/10 rounded-md px-1.5 text-xs text-white/70 focus:outline-none"
            >
              {FIELD_TYPES.map((t) => (
                <option key={t} value={t} className="bg-[#1a1a2e]">{t}</option>
              ))}
            </select>
            <button
              onClick={addResField}
              className="bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 rounded-md px-2 transition-colors"
            >
              <Plus className="w-3 h-3" />
            </button>
          </div>
        </div>
      </div>

      <Handle
        type="source"
        id="output"
        position={Position.Right}
        className="!bg-blue-500 !border-blue-300 !w-3 !h-3"
        title="Output"
      />
      <span className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-full pl-2 text-[9px] font-semibold uppercase tracking-wider text-white/50 whitespace-nowrap pointer-events-none">Output</span>
    </div>
    </NodeWrapper>
  );
}
