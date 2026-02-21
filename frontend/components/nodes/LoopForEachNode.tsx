"use client";

import { Handle, Position, useReactFlow } from "reactflow";
import { useCallback, useState } from "react";
import { Repeat } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import NodeWrapper from "./NodeWrapper";
import FieldModeInput, { FieldMode } from "./FieldModeInput";

interface ModeValue { mode: FieldMode; value: string; }

export default function LoopForEachNode({ id, data, selected }: any) {
  const { setNodes } = useReactFlow();
  const [nodeName, setNodeName] = useState(data.label || "Loop ForEach");
  const [arrayField, setArrayField] = useState<ModeValue>({
    mode: data.config?.array_field_mode || "expression",
    value: data.config?.array_field || "items",
  });

  const syncConfig = useCallback(
    (af: ModeValue, lbl?: string) => {
      setNodes((nds) =>
        nds.map((node) =>
          node.id === id
            ? {
                ...node,
                data: {
                  ...node.data,
                  label: lbl ?? node.data.label,
                  component: "loop_foreach",
                  config: { ...node.data.config, array_field: af.value, array_field_mode: af.mode },
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
            ? { ...node, data: { ...node.data, component: "loop_foreach", config: { ...node.data.config, array_field: arrayField.value, array_field_mode: arrayField.mode } } }
            : node
        )
      );
    });
  }

  const handleNameChange = (n: string) => { setNodeName(n); syncConfig(arrayField, n); };

  return (
    <NodeWrapper id={id} name={nodeName} onNameChange={handleNameChange} accentColor="cyan">
      <div className={`bg-[#1a1a2e] border rounded-xl shadow-2xl shadow-cyan-500/5 w-80 overflow-hidden relative ${selected ? "border-cyan-400 ring-1 ring-cyan-400/30" : "border-cyan-500/30"}`}>
        <div className="flex items-center gap-2 px-4 py-3 bg-cyan-500/10 border-b border-cyan-500/20">
          <Repeat className="w-4 h-4 text-cyan-400" />
          <span className="text-sm font-semibold text-cyan-300">{nodeName}</span>
          <Badge variant="outline" className="ml-auto text-[10px] px-1.5 py-0 bg-cyan-500/20 text-cyan-400 border-cyan-500/30 font-mono">
            {arrayField.value}
          </Badge>
        </div>

        <div className="p-4 space-y-3">
          <div>
            <div className="text-[10px] uppercase tracking-widest text-white/30 font-semibold mb-1.5">Array Field</div>
            <FieldModeInput
              mode={arrayField.mode}
              value={arrayField.value}
              onModeChange={(mode) => { const u = { mode, value: "" }; setArrayField(u); syncConfig(u); }}
              onValueChange={(value) => { const u = { ...arrayField, value }; setArrayField(u); syncConfig(u); }}
              placeholder={{ static: "items", input: "input.items", expression: "input.data.results" }}
            />
          </div>

          <div className="bg-white/[0.03] border border-white/[0.06] rounded-lg p-3 space-y-2">
            <div className="text-[9px] uppercase tracking-widest text-white/25 font-semibold">Handles</div>
            <div className="grid grid-cols-2 gap-2 text-[10px]">
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full bg-cyan-500" />
                <span className="text-white/50">IN</span>
                <span className="text-white/25">data with array</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full bg-cyan-400" />
                <span className="text-white/50">LOOP OUT</span>
                <span className="text-white/25">each element</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full bg-cyan-600" />
                <span className="text-white/50">BACK</span>
                <span className="text-white/25">body result</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full bg-emerald-500" />
                <span className="text-white/50">DONE</span>
                <span className="text-white/25">all results</span>
              </div>
            </div>
          </div>
        </div>

        <Handle type="target" position={Position.Left} id="in" style={{ top: "30%" }} className="!bg-cyan-500 !border-cyan-300 !w-3 !h-3" title="Input" />
        <span className="absolute left-0 top-[30%] -translate-y-1/2 -translate-x-full pr-2 text-[9px] font-semibold uppercase tracking-wider text-white/50 whitespace-nowrap pointer-events-none">Input</span>
        <Handle type="target" position={Position.Left} id="loop_back" style={{ top: "75%" }} className="!bg-cyan-600 !border-cyan-400 !w-3 !h-3" title="Loop back" />
        <span className="absolute left-0 top-[75%] -translate-y-1/2 -translate-x-full pr-2 text-[9px] font-semibold uppercase tracking-wider text-white/50 whitespace-nowrap pointer-events-none">Loop back</span>
        <Handle type="source" position={Position.Right} id="loop_out" style={{ top: "30%" }} className="!bg-cyan-400 !border-cyan-200 !w-3 !h-3" title="Loop out" />
        <span className="absolute right-0 top-[30%] -translate-y-1/2 translate-x-full pl-2 text-[9px] font-semibold uppercase tracking-wider text-white/50 whitespace-nowrap pointer-events-none">Loop out</span>
        <Handle type="source" position={Position.Right} id="done" style={{ top: "75%" }} className="!bg-emerald-500 !border-emerald-300 !w-3 !h-3" title="Done" />
        <span className="absolute right-0 top-[75%] -translate-y-1/2 translate-x-full pl-2 text-[9px] font-semibold uppercase tracking-wider text-white/50 whitespace-nowrap pointer-events-none">Done</span>
      </div>
    </NodeWrapper>
  );
}
