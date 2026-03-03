"use client";

import { Handle, Position, useReactFlow } from "reactflow";
import { useState } from "react";
import { GitFork } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import NodeWrapper from "./NodeWrapper";

export default function ParallelSplitNode({ id, data, selected }: any) {
  const { setNodes } = useReactFlow();
  const [nodeName, setNodeName] = useState(data.label || "Parallel Split");

  if (!data.component) {
    queueMicrotask(() => {
      setNodes((nds) =>
        nds.map((node) =>
          node.id === id
            ? { ...node, data: { ...node.data, component: "parallel_split" } }
            : node
        )
      );
    });
  }

  const handleNameChange = (n: string) => {
    setNodeName(n);
    setNodes((nds) =>
      nds.map((node) =>
        node.id === id ? { ...node, data: { ...node.data, label: n, component: "parallel_split" } } : node
      )
    );
  };

  return (
    <NodeWrapper id={id} name={nodeName} onNameChange={handleNameChange} accentColor="sky">
      <div className={`bg-[#1a1a2e] border rounded-xl shadow-2xl shadow-sky-500/5 w-64 relative overflow-visible ${selected ? "border-sky-400 ring-1 ring-sky-400/30" : "border-sky-500/30"}`}>
        <div className="flex items-center gap-2 px-4 py-3 bg-sky-500/10 border-b border-sky-500/20">
          <GitFork className="w-4 h-4 text-sky-400" />
          <span className="text-sm font-semibold text-sky-300">{nodeName}</span>
          <Badge variant="outline" className="ml-auto text-[10px] px-1.5 py-0 bg-sky-500/20 text-sky-400 border-sky-500/30">
            Fork
          </Badge>
        </div>
        <div className="p-4">
          <div className="bg-white/5 rounded-lg px-3 py-2">
            <p className="text-xs text-white/50 leading-relaxed">
              Runs all downstream children concurrently. Connect multiple outputs to process in parallel.
            </p>
          </div>
        </div>
        <Handle type="target" id="input" position={Position.Left} className="!bg-sky-500 !border-sky-300 !w-3 !h-3" title="Input" />
        <span className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-full pr-2 text-[9px] font-semibold uppercase tracking-wider text-white/50 whitespace-nowrap pointer-events-none">Input</span>
        <Handle type="source" id="output" position={Position.Right} className="!bg-sky-500 !border-sky-300 !w-3 !h-3" title="Output" />
        <span className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-full pl-2 text-[9px] font-semibold uppercase tracking-wider text-white/50 whitespace-nowrap pointer-events-none">Output</span>
      </div>
    </NodeWrapper>
  );
}
