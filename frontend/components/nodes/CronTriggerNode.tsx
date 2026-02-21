"use client";

import { Handle, Position, useReactFlow } from "reactflow";
import { useCallback, useState } from "react";
import { Clock } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import NodeWrapper from "./NodeWrapper";

export default function CronTriggerNode({ id, data, selected }: any) {
  const { setNodes } = useReactFlow();
  const [nodeName, setNodeName] = useState(data.label || "Cron Trigger");
  const [cronExpr, setCronExpr] = useState<string>(data.config?.cron_expression || "* * * * *");

  const syncConfig = useCallback(
    (expr: string, lbl?: string) => {
      setNodes((nds) =>
        nds.map((node) =>
          node.id === id
            ? {
                ...node,
                data: {
                  ...node.data,
                  label: lbl ?? node.data.label,
                  component: "cron_trigger",
                  config: { ...node.data.config, is_entry: true, cron_expression: expr },
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
            ? { ...node, data: { ...node.data, component: "cron_trigger", config: { ...node.data.config, is_entry: true, cron_expression: cronExpr } } }
            : node
        )
      );
    });
  }

  const handleCronChange = (val: string) => {
    setCronExpr(val);
    syncConfig(val);
  };

  const handleNameChange = (n: string) => {
    setNodeName(n);
    syncConfig(cronExpr, n);
  };

  return (
    <NodeWrapper id={id} name={nodeName} onNameChange={handleNameChange} accentColor="yellow">
      <div className={`bg-[#1a1a2e] border rounded-xl shadow-2xl shadow-yellow-500/5 w-72 relative overflow-visible ${selected ? "border-yellow-400 ring-1 ring-yellow-400/30" : "border-yellow-500/30"}`}>
        <div className="flex items-center gap-2 px-4 py-3 bg-yellow-500/10 border-b border-yellow-500/20">
          <Clock className="w-4 h-4 text-yellow-400" />
          <span className="text-sm font-semibold text-yellow-300">{nodeName}</span>
          <Badge variant="outline" className="ml-auto text-[10px] px-1.5 py-0 bg-yellow-500/20 text-yellow-400 border-yellow-500/30">
            Scheduled
          </Badge>
        </div>
        <div className="p-4 space-y-3">
          <div>
            <div className="text-[10px] uppercase tracking-widest text-white/30 font-semibold mb-1.5">Cron Expression</div>
            <input
              value={cronExpr}
              onChange={(e) => handleCronChange(e.target.value)}
              placeholder="* * * * *"
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-white/30 focus:outline-none focus:border-yellow-500/50 font-mono"
            />
          </div>
          <div className="bg-white/5 rounded-lg px-3 py-2 space-y-1">
            <div className="text-[10px] uppercase tracking-widest text-white/30 font-semibold">Format</div>
            <p className="text-[10px] text-white/40 font-mono leading-relaxed">min hour day month weekday</p>
          </div>
        </div>
        <Handle type="source" id="output" position={Position.Right} className="!bg-yellow-500 !border-yellow-300 !w-3 !h-3" title="Output" />
        <span className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-full pl-2 text-[9px] font-semibold uppercase tracking-wider text-white/50 whitespace-nowrap pointer-events-none">Output</span>
      </div>
    </NodeWrapper>
  );
}
