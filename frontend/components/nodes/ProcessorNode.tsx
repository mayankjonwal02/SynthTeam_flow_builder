"use client";

import { Handle, Position, useReactFlow } from "reactflow";
import { useCallback, useState } from "react";
import { Cpu, Zap } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import NodeWrapper from "./NodeWrapper";

export default function ProcessorNode({ id, data, selected }: any) {
  const { setNodes } = useReactFlow();

  const [nodeName, setNodeName] = useState(data.label || "Processor");
  const [label, setLabel] = useState<string>(
    data.config?.label || "Echo Processor"
  );

  // ── immutable state update via setNodes ──
  const syncConfig = useCallback(
    (newLabel: string, lbl?: string) => {
      setNodes((nds) =>
        nds.map((node) =>
          node.id === id
            ? {
                ...node,
                data: {
                  ...node.data,
                  label: lbl ?? node.data.label,
                  component: "echo_processor",
                  config: {
                    ...node.data.config,
                    label: newLabel,
                  },
                },
              }
            : node
        )
      );
    },
    [id, setNodes]
  );

  // Ensure component name is set on first render
  if (!data.component) {
    queueMicrotask(() => {
      setNodes((nds) =>
        nds.map((node) =>
          node.id === id
            ? {
                ...node,
                data: {
                  ...node.data,
                  component: "echo_processor",
                  config: { ...node.data.config, label },
                },
              }
            : node
        )
      );
    });
  }

  const handleLabelChange = (value: string) => {
    setLabel(value);
    syncConfig(value);
  };

  const handleNameChange = (n: string) => {
    setNodeName(n);
    syncConfig(label, n);
  };

  return (
    <NodeWrapper id={id} name={nodeName} onNameChange={handleNameChange} accentColor="amber">
    <div className={`bg-[#1a1a2e] border rounded-xl shadow-2xl shadow-amber-500/5 w-72 overflow-hidden ${selected ? "border-amber-400 ring-1 ring-amber-400/30" : "border-amber-500/30"}`}>
      {/* ── header ── */}
      <div className="flex items-center gap-2 px-4 py-3 bg-amber-500/10 border-b border-amber-500/20">
        <Cpu className="w-4 h-4 text-amber-400" />
        <span className="text-sm font-semibold text-amber-300">{nodeName}</span>
        <Badge
          variant="outline"
          className="ml-auto text-[10px] px-1.5 py-0 bg-amber-500/20 text-amber-400 border-amber-500/30"
        >
          <Zap className="w-2.5 h-2.5 mr-0.5" />
          Transform
        </Badge>
      </div>

      <div className="p-4 space-y-3">
        {/* ── label ── */}
        <input
          value={label}
          onChange={(e) => handleLabelChange(e.target.value)}
          placeholder="Processor label"
          className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-white/30 focus:outline-none focus:border-amber-500/50"
        />

        {/* ── description ── */}
        <div className="bg-white/5 rounded-lg px-3 py-2 space-y-1">
          <div className="text-[10px] uppercase tracking-widest text-white/30 font-semibold">
            Behavior
          </div>
          <p className="text-xs text-white/50 leading-relaxed">
            Merges all upstream inputs and passes them through.
            Connect upstream → downstream to relay data.
          </p>
        </div>

        {/* ── I/O indicators ── */}
        <div className="flex gap-2">
          <div className="flex-1 bg-white/5 rounded-lg px-3 py-2 text-center">
            <div className="text-[10px] text-white/30">INPUT</div>
            <div className="text-xs text-amber-400 font-mono">any</div>
          </div>
          <div className="flex-1 bg-white/5 rounded-lg px-3 py-2 text-center">
            <div className="text-[10px] text-white/30">OUTPUT</div>
            <div className="text-xs text-amber-400 font-mono">merged</div>
          </div>
        </div>
      </div>

      <Handle
        type="target"
        position={Position.Left}
        className="!bg-amber-500 !border-amber-300 !w-3 !h-3"
      />
      <Handle
        type="source"
        position={Position.Right}
        className="!bg-amber-500 !border-amber-300 !w-3 !h-3"
      />
    </div>
    </NodeWrapper>
  );
}
