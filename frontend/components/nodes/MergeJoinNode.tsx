"use client";

import { Handle, Position, useReactFlow } from "reactflow";
import { useState } from "react";
import { Merge } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import NodeWrapper from "./NodeWrapper";

export default function MergeJoinNode({ id, data, selected }: any) {
  const { setNodes } = useReactFlow();
  const [nodeName, setNodeName] = useState(data.label || "Merge / Join");

  if (!data.component) {
    queueMicrotask(() => {
      setNodes((nds) =>
        nds.map((node) =>
          node.id === id
            ? { ...node, data: { ...node.data, component: "merge_join" } }
            : node
        )
      );
    });
  }

  const handleNameChange = (n: string) => {
    setNodeName(n);
    setNodes((nds) =>
      nds.map((node) =>
        node.id === id ? { ...node, data: { ...node.data, label: n, component: "merge_join" } } : node
      )
    );
  };

  return (
    <NodeWrapper id={id} name={nodeName} onNameChange={handleNameChange} accentColor="teal">
      <div className={`bg-[#1a1a2e] border rounded-xl shadow-2xl shadow-teal-500/5 w-64 overflow-hidden ${selected ? "border-teal-400 ring-1 ring-teal-400/30" : "border-teal-500/30"}`}>
        <div className="flex items-center gap-2 px-4 py-3 bg-teal-500/10 border-b border-teal-500/20">
          <Merge className="w-4 h-4 text-teal-400" />
          <span className="text-sm font-semibold text-teal-300">{nodeName}</span>
          <Badge variant="outline" className="ml-auto text-[10px] px-1.5 py-0 bg-teal-500/20 text-teal-400 border-teal-500/30">
            Join
          </Badge>
        </div>
        <div className="p-4">
          <div className="bg-white/5 rounded-lg px-3 py-2">
            <p className="text-xs text-white/50 leading-relaxed">
              Waits for all parent nodes to complete, then merges their outputs into a single dict.
            </p>
          </div>
        </div>
        <Handle type="target" position={Position.Left} className="!bg-teal-500 !border-teal-300 !w-3 !h-3" />
        <Handle type="source" position={Position.Right} className="!bg-teal-500 !border-teal-300 !w-3 !h-3" />
      </div>
    </NodeWrapper>
  );
}
