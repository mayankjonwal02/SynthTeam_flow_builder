"use client";

import { Handle, Position, useReactFlow } from "reactflow";
import { useCallback, useState } from "react";
import { Code2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import NodeWrapper from "./NodeWrapper";

const DEFAULT_BODY = `# data = merged upstream inputs (dict)
# return a dict
return {"result": data}`;

export default function PythonFunctionNode({ id, data, selected }: any) {
  const { setNodes } = useReactFlow();
  const [nodeName, setNodeName] = useState(data.label || "Python Function");
  const [code, setCode] = useState<string>(data.config?.code || DEFAULT_BODY);

  const syncConfig = useCallback(
    (c: string, lbl?: string) => {
      setNodes((nds) =>
        nds.map((node) =>
          node.id === id
            ? {
                ...node,
                data: {
                  ...node.data,
                  label: lbl ?? node.data.label,
                  component: "python_function",
                  config: { ...node.data.config, code: c },
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
            ? {
                ...node,
                data: {
                  ...node.data,
                  component: "python_function",
                  config: { ...node.data.config, code },
                },
              }
            : node
        )
      );
    });
  }

  const handleCodeChange = (val: string) => {
    setCode(val);
    syncConfig(val);
  };

  const handleNameChange = (n: string) => {
    setNodeName(n);
    syncConfig(code, n);
  };

  const lineCount = code.split("\n").length;

  return (
    <NodeWrapper id={id} name={nodeName} onNameChange={handleNameChange} accentColor="fuchsia">
      <div
        className={`bg-[#1a1a2e] border rounded-xl shadow-2xl shadow-fuchsia-500/5 w-[340px] relative overflow-visible ${
          selected
            ? "border-fuchsia-400 ring-1 ring-fuchsia-400/30"
            : "border-fuchsia-500/30"
        }`}
      >
        <div className="flex items-center gap-2 px-4 py-3 bg-fuchsia-500/10 border-b border-fuchsia-500/20">
          <Code2 className="w-4 h-4 text-fuchsia-400" />
          <span className="text-sm font-semibold text-fuchsia-300">
            {nodeName}
          </span>
          <Badge
            variant="outline"
            className="ml-auto text-[10px] px-1.5 py-0 bg-fuchsia-500/20 text-fuchsia-400 border-fuchsia-500/30"
          >
            {lineCount} lines
          </Badge>
        </div>

        <div className="p-4 space-y-2">
          {/* fixed function signature */}
          <div className="bg-black/40 border border-white/10 rounded-t-lg px-3 py-1.5 font-mono text-xs text-fuchsia-400/70">
            def handler(data):
          </div>
          {/* user edits the body only */}
          <textarea
            value={code}
            onChange={(e) => handleCodeChange(e.target.value)}
            spellCheck={false}
            rows={6}
            className="w-full bg-black/40 border border-white/10 border-t-0 rounded-b-lg px-3 py-2 text-xs text-fuchsia-200 placeholder-white/20 focus:outline-none focus:border-fuchsia-500/50 font-mono leading-relaxed resize-y pl-7"
            placeholder={DEFAULT_BODY}
          />
          <div className="bg-white/5 rounded-lg px-3 py-1.5">
            <p className="text-[10px] text-white/30 leading-relaxed">
              <span className="text-fuchsia-400/60">data</span> = merged upstream outputs (dict). Return a dict to pass downstream.
            </p>
          </div>
        </div>

        <Handle type="target" id="input" position={Position.Left} className="!bg-fuchsia-500 !border-fuchsia-300 !w-3 !h-3" title="Input" />
        <span className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-full pr-2 text-[9px] font-semibold uppercase tracking-wider text-white/50 whitespace-nowrap pointer-events-none">Input</span>
        <Handle type="source" id="output" position={Position.Right} className="!bg-fuchsia-500 !border-fuchsia-300 !w-3 !h-3" title="Output" />
        <span className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-full pl-2 text-[9px] font-semibold uppercase tracking-wider text-white/50 whitespace-nowrap pointer-events-none">Output</span>
      </div>
    </NodeWrapper>
  );
}
