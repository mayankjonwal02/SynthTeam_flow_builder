"use client";

import { useCallback } from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  BackgroundVariant,
  useNodesState,
  useEdgesState,
  Node,
  Edge,
  ReactFlowProvider,
} from "reactflow";
import "reactflow/dist/style.css";
import { nodeTypes } from "@/components/nodes/nodeTypes";
import { motion, AnimatePresence } from "framer-motion";

interface Props {
  nodes: Node[];
  edges: Edge[];
  onNodesChange?: (nodes: Node[]) => void;
  onEdgesChange?: (edges: Edge[]) => void;
}

function AnimatedNode({ data, ...props }: any) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.7, y: 20 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
    >
      {data?.label || "Node"}
    </motion.div>
  );
}

function CanvasInner({ nodes, edges }: Props) {
  const [rfNodes, setRfNodes, onNodesChange] = useNodesState(nodes);
  const [rfEdges, setRfEdges, onEdgesChange] = useEdgesState(edges);

  const updateFromProps = useCallback(
    (newNodes: Node[], newEdges: Edge[]) => {
      setRfNodes(newNodes);
      setRfEdges(newEdges);
    },
    [setRfNodes, setRfEdges]
  );

  if (
    (nodes.length !== rfNodes.length || edges.length !== rfEdges.length) ||
    (nodes.length > 0 && rfNodes.length === 0)
  ) {
    updateFromProps(nodes, edges);
  }

  return (
    <div className="w-full h-full bg-[#0a0a12]">
      <ReactFlow
        nodes={rfNodes}
        edges={rfEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.3 }}
        proOptions={{ hideAttribution: true }}
        className="!bg-[#0a0a12]"
      >
        <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="rgba(255,255,255,0.04)" />
        <Controls className="!bg-white/10 !border-white/10 !rounded-lg [&>button]:!bg-white/10 [&>button]:!border-white/5 [&>button]:!text-white/60" />
        <MiniMap
          nodeColor={() => "#6366f1"}
          maskColor="rgba(0,0,0,0.7)"
          className="!bg-black/40 !border-white/10 !rounded-lg"
        />
      </ReactFlow>

      {rfNodes.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="text-center space-y-2">
            <div className="text-white/20 text-lg font-medium">Workflow Canvas</div>
            <div className="text-white/10 text-sm">Nodes will appear here as the Builder agent works</div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function AgentCanvas(props: Props) {
  return (
    <ReactFlowProvider>
      <CanvasInner {...props} />
    </ReactFlowProvider>
  );
}
