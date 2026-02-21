"use client";

import { Handle, Position, useReactFlow } from "reactflow";
import { useCallback, useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import NodeWrapper from "../NodeWrapper";
import FieldModeInput, { FieldMode } from "../FieldModeInput";

interface FilterField { 
  key: string; 
  mode: FieldMode;
  value: string; 
}

type FieldType = "connection_id" | "database" | "table" | "collection" | "filters" | "filter" | "query" | "pipeline";

interface DBNodeConfig {
  componentName: string;
  defaultLabel: string;
  accentColor: string;
  accentClasses: { border: string; bg: string; text: string; shadow: string };
  opBadge: string;
  icon: any;
  fields: FieldType[];
}

export function createDBNode(cfg: DBNodeConfig) {
  return function DBNodeInstance({ id, data, selected }: any) {
    const { setNodes } = useReactFlow();
    const [nodeName, setNodeName] = useState(data.label || cfg.defaultLabel);
    const [connId, setConnId] = useState<string>(data.config?.connection_id || "");
    const [database, setDatabase] = useState<string>(data.config?.database || "");
    const [tableOrColl, setTableOrColl] = useState<string>(
      data.config?.table || data.config?.collection || ""
    );
    const [query, setQuery] = useState<string>(
      data.config?.query || data.config?.pipeline || ""
    );
    const [filters, setFilters] = useState<FilterField[]>(() => {
      const filterMappings = data.config?.filter_mappings;
      if (filterMappings) return filterMappings;
      const f = data.config?.filters || data.config?.filter || {};
      return Object.entries(f).map(([k, v]) => ({ key: k, mode: "expression" as FieldMode, value: v as string }));
    });
    const [newKey, setNewKey] = useState("");
    const [newMode, setNewMode] = useState<FieldMode>("expression");

    const hasField = (f: FieldType) => cfg.fields.includes(f);
    const tableKey = hasField("collection") ? "collection" : "table";
    const filterKey = hasField("filter") ? "filter" : "filters";
    const queryKey = hasField("pipeline") ? "pipeline" : "query";

    const syncConfig = useCallback(
      (cid: string, db: string, tbl: string, f: FilterField[], q: string, lbl?: string) => {
        const config: any = { connection_id: cid };
        if (hasField("database")) config.database = db;
        if (hasField("table") || hasField("collection")) config[tableKey] = tbl;
        if (hasField("filters") || hasField("filter")) {
          config.filter_mappings = f;
        }
        if (hasField("query") || hasField("pipeline")) config[queryKey] = q;
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

    const addFilter = () => {
      if (!newKey.trim()) return;
      const u = [...filters, { key: newKey.trim(), mode: newMode, value: "" }];
      setFilters(u);
      syncConfig(connId, database, tableOrColl, u, query);
      setNewKey("");
      setNewMode("expression");
    };
    const removeFilter = (i: number) => {
      const u = filters.filter((_, idx) => idx !== i);
      setFilters(u);
      syncConfig(connId, database, tableOrColl, u, query);
    };
    const updateFilter = (i: number, patch: Partial<FilterField>) => {
      const u = filters.map((f, idx) => (idx === i ? { ...f, ...patch } : f));
      setFilters(u);
      syncConfig(connId, database, tableOrColl, u, query);
    };

    const Icon = cfg.icon;
    const ac = cfg.accentClasses;

    return (
      <NodeWrapper id={id} name={nodeName} onNameChange={(n) => { setNodeName(n); syncConfig(connId, database, tableOrColl, filters, query, n); }} accentColor={cfg.accentColor}>
        <div className={`bg-[#1a1a2e] border rounded-xl shadow-2xl ${ac.shadow} w-80 relative overflow-visible ${selected ? `${ac.border} ring-1 ring-${cfg.accentColor}-400/30` : ac.border.replace("border-", "border-").replace("400", "500/30")}`}>
          <div className={`flex items-center gap-2 px-4 py-3 ${ac.bg} border-b ${ac.border.replace("400", "500/20")}`}>
            <Icon className={`w-4 h-4 ${ac.text}`} />
            <span className={`text-sm font-semibold ${ac.text.replace("400", "300")}`}>{nodeName}</span>
            <Badge variant="outline" className={`ml-auto text-[10px] px-1.5 py-0 ${ac.bg} ${ac.text} ${ac.border}`}>{cfg.opBadge}</Badge>
          </div>
          <div className="p-4 space-y-2.5">
            {hasField("connection_id") && (
              <div>
                <div className="text-[10px] uppercase tracking-widest text-white/30 font-semibold mb-1">Connection URI</div>
                <input value={connId} onChange={(e) => { setConnId(e.target.value); syncConfig(e.target.value, database, tableOrColl, filters, query); }} placeholder="mongodb+srv://... or postgresql://..." className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white placeholder-white/25 focus:outline-none font-mono" />
              </div>
            )}
            {hasField("database") && (
              <div>
                <div className="text-[10px] uppercase tracking-widest text-white/30 font-semibold mb-1">Database</div>
                <input value={database} onChange={(e) => { setDatabase(e.target.value); syncConfig(connId, e.target.value, tableOrColl, filters, query); }} placeholder="my_database" className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white placeholder-white/25 focus:outline-none font-mono" />
              </div>
            )}
            {(hasField("table") || hasField("collection")) && (
              <div>
                <div className="text-[10px] uppercase tracking-widest text-white/30 font-semibold mb-1">{hasField("collection") ? "Collection" : "Table"}</div>
                <input value={tableOrColl} onChange={(e) => { setTableOrColl(e.target.value); syncConfig(connId, database, e.target.value, filters, query); }} placeholder={hasField("collection") ? "users" : "users"} className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white placeholder-white/25 focus:outline-none font-mono" />
              </div>
            )}
            {(hasField("filters") || hasField("filter")) && (
              <div className="space-y-1.5">
                <div className="text-[10px] uppercase tracking-widest text-white/30 font-semibold">{hasField("filter") ? "Filter" : "Filters"}</div>
                {filters.map((f, i) => (
                  <div key={i} className="bg-white/[0.03] border border-white/[0.06] rounded-lg p-2 space-y-1.5 group">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] text-white/70 font-mono font-medium flex-1">{f.key}</span>
                      <button onClick={() => removeFilter(i)} className="opacity-0 group-hover:opacity-100 text-red-400"><Trash2 className="w-3 h-3" /></button>
                    </div>
                    <FieldModeInput
                      mode={f.mode}
                      value={f.value}
                      onModeChange={(mode) => updateFilter(i, { mode, value: "" })}
                      onValueChange={(value) => updateFilter(i, { value })}
                      placeholder={{
                        static: "fixed value",
                        input: "input.fieldName",
                        expression: "input.data.id",
                      }}
                    />
                  </div>
                ))}
                <div className="flex gap-1">
                  <input value={newKey} onChange={(e) => setNewKey(e.target.value)} onKeyDown={(e) => e.key === "Enter" && addFilter()} placeholder="field name" className="flex-1 bg-white/5 border border-white/10 rounded-md px-2 py-1 text-[10px] text-white font-mono focus:outline-none" />
                  <button onClick={addFilter} className={`${ac.bg} hover:opacity-80 ${ac.text} rounded-md px-2`}><Plus className="w-3 h-3" /></button>
                </div>
              </div>
            )}
            {(hasField("query") || hasField("pipeline")) && (
              <div>
                <div className="text-[10px] uppercase tracking-widest text-white/30 font-semibold mb-1">{hasField("pipeline") ? "Pipeline (JSON)" : "Query"}</div>
                <textarea value={query} onChange={(e) => { setQuery(e.target.value); syncConfig(connId, database, tableOrColl, filters, e.target.value); }} rows={3} spellCheck={false} placeholder={hasField("pipeline") ? '[{"$match": {...}}]' : "SELECT * FROM ..."} className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white placeholder-white/20 focus:outline-none font-mono resize-y" />
              </div>
            )}
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
