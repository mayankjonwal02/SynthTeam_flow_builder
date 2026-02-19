"use client";

import { Handle, Position, useReactFlow } from "reactflow";
import { useState } from "react";
import { Play } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import NodeWrapper from "./NodeWrapper";

export default function ManualTriggerNode({ id, data, selected }: any) {
  const { setNodes } = useReactFlow();
  const [nodeName, setNodeName] = useState(data.label || "Manual Trigger");

  if (!data.component) {
    queueMicrotask(() => {
      setNodes((nds) =>
        nds.map((node) =>
          node.id === id
            ? { ...node, data: { ...node.data, component: "manual_trigger", config: { ...node.data.config, is_entry: true } } }
            : node
        )
      );
    });
  }

  const handleNameChange = (n: string) => {
    setNodeName(n);
    setNodes((nds) =>
      nds.map((node) =>
        node.id === id ? { ...node, data: { ...node.data, label: n, component: "manual_trigger", config: { ...node.data.config, is_entry: true } } } : node
      )
    );
  };

  return (
    <NodeWrapper id={id} name={nodeName} onNameChange={handleNameChange} accentColor="lime">
      <div className={`bg-[#1a1a2e] border rounded-xl shadow-2xl shadow-lime-500/5 w-64 overflow-hidden ${selected ? "border-lime-400 ring-1 ring-lime-400/30" : "border-lime-500/30"}`}>
        <div className="flex items-center gap-2 px-4 py-3 bg-lime-500/10 border-b border-lime-500/20">
          <Play className="w-4 h-4 text-lime-400" />
          <span className="text-sm font-semibold text-lime-300">{nodeName}</span>
          <Badge variant="outline" className="ml-auto text-[10px] px-1.5 py-0 bg-lime-500/20 text-lime-400 border-lime-500/30">
            Entry
          </Badge>
        </div>
        <div className="p-4">
          <div className="bg-white/5 rounded-lg px-3 py-2">
            <p className="text-xs text-white/50 leading-relaxed">
              Manual entry point for testing. Passes the full request body through without filtering.
            </p>
          </div>
        </div>
        <Handle type="source" position={Position.Right} className="!bg-lime-500 !border-lime-300 !w-3 !h-3" />
      </div>
    </NodeWrapper>
  );
}
