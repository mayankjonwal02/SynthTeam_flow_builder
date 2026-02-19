"use client";

import { Handle, Position, useReactFlow } from "reactflow";
import { useCallback, useState } from "react";
import { Timer } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import NodeWrapper from "./NodeWrapper";

export default function DelayNode({ id, data, selected }: any) {
  const { setNodes } = useReactFlow();
  const [nodeName, setNodeName] = useState(data.label || "Delay");
  const [seconds, setSeconds] = useState<number>(data.config?.seconds ?? 1);

  const syncConfig = useCallback(
    (s: number, lbl?: string) => {
      setNodes((nds) =>
        nds.map((node) =>
          node.id === id
            ? {
                ...node,
                data: {
                  ...node.data,
                  label: lbl ?? node.data.label,
                  component: "delay",
                  config: { ...node.data.config, seconds: s },
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
            ? { ...node, data: { ...node.data, component: "delay", config: { ...node.data.config, seconds } } }
            : node
        )
      );
    });
  }

  const handleSecondsChange = (val: string) => {
    const n = Math.max(0, Number(val) || 0);
    setSeconds(n);
    syncConfig(n);
  };

  const handleNameChange = (n: string) => {
    setNodeName(n);
    syncConfig(seconds, n);
  };

  return (
    <NodeWrapper id={id} name={nodeName} onNameChange={handleNameChange} accentColor="orange">
      <div className={`bg-[#1a1a2e] border rounded-xl shadow-2xl shadow-orange-500/5 w-64 overflow-hidden ${selected ? "border-orange-400 ring-1 ring-orange-400/30" : "border-orange-500/30"}`}>
        <div className="flex items-center gap-2 px-4 py-3 bg-orange-500/10 border-b border-orange-500/20">
          <Timer className="w-4 h-4 text-orange-400" />
          <span className="text-sm font-semibold text-orange-300">{nodeName}</span>
          <Badge variant="outline" className="ml-auto text-[10px] px-1.5 py-0 bg-orange-500/20 text-orange-400 border-orange-500/30">
            {seconds}s
          </Badge>
        </div>
        <div className="p-4 space-y-3">
          <div>
            <div className="text-[10px] uppercase tracking-widest text-white/30 font-semibold mb-1.5">Delay (seconds)</div>
            <input
              type="number"
              min={0}
              step={0.5}
              value={seconds}
              onChange={(e) => handleSecondsChange(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-white/30 focus:outline-none focus:border-orange-500/50 font-mono"
            />
          </div>
          <div className="bg-white/5 rounded-lg px-3 py-2">
            <p className="text-xs text-white/50 leading-relaxed">
              Pauses execution for the configured duration then passes data through.
            </p>
          </div>
        </div>
        <Handle type="target" position={Position.Left} className="!bg-orange-500 !border-orange-300 !w-3 !h-3" />
        <Handle type="source" position={Position.Right} className="!bg-orange-500 !border-orange-300 !w-3 !h-3" />
      </div>
    </NodeWrapper>
  );
}
