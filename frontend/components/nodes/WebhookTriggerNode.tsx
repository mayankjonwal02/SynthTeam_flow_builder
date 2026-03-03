"use client";

import { Handle, Position, useReactFlow } from "reactflow";
import { useCallback, useState } from "react";
import { Webhook } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import NodeWrapper from "./NodeWrapper";

export default function WebhookTriggerNode({ id, data, selected }: any) {
  const { setNodes } = useReactFlow();
  const [nodeName, setNodeName] = useState(data.label || "Webhook Trigger");
  const [path, setPath] = useState<string>(data.config?.path || "/webhook/endpoint");

  const syncConfig = useCallback(
    (p: string, lbl?: string) => {
      setNodes((nds) =>
        nds.map((node) =>
          node.id === id
            ? {
                ...node,
                data: {
                  ...node.data,
                  label: lbl ?? node.data.label,
                  component: "webhook_trigger",
                  config: { ...node.data.config, is_entry: true, method: "POST", path: p },
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
            ? { ...node, data: { ...node.data, component: "webhook_trigger", config: { ...node.data.config, is_entry: true, method: "POST", path } } }
            : node
        )
      );
    });
  }

  const handlePathChange = (p: string) => {
    setPath(p);
    syncConfig(p);
  };

  const handleNameChange = (n: string) => {
    setNodeName(n);
    syncConfig(path, n);
  };

  return (
    <NodeWrapper id={id} name={nodeName} onNameChange={handleNameChange} accentColor="pink">
      <div className={`bg-[#1a1a2e] border rounded-xl shadow-2xl shadow-pink-500/5 w-72 relative overflow-visible ${selected ? "border-pink-400 ring-1 ring-pink-400/30" : "border-pink-500/30"}`}>
        <div className="flex items-center gap-2 px-4 py-3 bg-pink-500/10 border-b border-pink-500/20">
          <Webhook className="w-4 h-4 text-pink-400" />
          <span className="text-sm font-semibold text-pink-300">{nodeName}</span>
          <Badge variant="outline" className="ml-auto text-[10px] px-1.5 py-0 bg-pink-500/20 text-pink-400 border-pink-500/30">
            POST
          </Badge>
        </div>
        <div className="p-4 space-y-3">
          <div>
            <div className="text-[10px] uppercase tracking-widest text-white/30 font-semibold mb-1.5">Webhook Path</div>
            <input
              value={path}
              onChange={(e) => handlePathChange(e.target.value)}
              placeholder="/webhook/endpoint"
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-white/30 focus:outline-none focus:border-pink-500/50 font-mono"
            />
          </div>
          <div className="bg-white/5 rounded-lg px-3 py-2">
            <p className="text-xs text-white/50 leading-relaxed">
              Receives external POST requests at the configured path.
            </p>
          </div>
        </div>
        <Handle type="source" id="output" position={Position.Right} className="!bg-pink-500 !border-pink-300 !w-3 !h-3" title="Output" />
        <span className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-full pl-2 text-[9px] font-semibold uppercase tracking-wider text-white/50 whitespace-nowrap pointer-events-none">Output</span>
      </div>
    </NodeWrapper>
  );
}
