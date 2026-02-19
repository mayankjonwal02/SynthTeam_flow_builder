"use client";

import { use, useEffect, useState, useCallback, useRef } from "react";
import axios from "axios";
import { useAuth } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import ReactFlow, {
  useNodesState,
  useEdgesState,
  addEdge,
  Background,
  Controls,
  MiniMap,
  BackgroundVariant,
  Connection,
  ReactFlowProvider,
  ReactFlowInstance,
} from "reactflow";
import "reactflow/dist/style.css";
import { nodeTypes } from "@/components/nodes/nodeTypes";
import DeletableEdge from "@/components/edges/DeletableEdge";

import { toast } from "sonner";
import {
  ArrowLeft,
  Save,
  Rocket,
  Globe,
  Cpu,
  Send,
  Layers,
  Grip,
  Loader2,
  Square,
  Circle,
  GitBranch,
  Route,
  Repeat,
  GitFork,
  Merge,
  Timer,
  Webhook,
  Clock,
  Play,
  FileSearch,
  ShieldCheck,
  Code2,
  ScrollText,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import ExecutionDrawer from "@/components/ExecutionDrawer";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";

const edgeTypes = { deletable: DeletableEdge };

const rfStyle = { backgroundColor: "#0a0a0f" };

// ── palette definition with sections ────────────────────────────────
interface PaletteItem {
  type: string;
  label: string;
  description: string;
  icon: any;
  accent: string;
}

interface PaletteSection {
  title: string;
  items: PaletteItem[];
}

const PALETTE_SECTIONS: PaletteSection[] = [
  {
    title: "Triggers",
    items: [
      { type: "http_entry",      label: "HTTP Entry",      description: "API endpoint entry point",     icon: Globe,    accent: "bg-blue-500/20 text-blue-400 border-blue-500/30" },
      { type: "webhook_trigger", label: "Webhook",         description: "Receive external webhooks",    icon: Webhook,  accent: "bg-pink-500/20 text-pink-400 border-pink-500/30" },
      { type: "cron_trigger",    label: "Cron Schedule",   description: "Time-based trigger",           icon: Clock,    accent: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30" },
      { type: "manual_trigger",  label: "Manual Trigger",  description: "Test entry point",             icon: Play,     accent: "bg-lime-500/20 text-lime-400 border-lime-500/30" },
    ],
  },
  {
    title: "Logic",
    items: [
      { type: "if_condition",    label: "If Condition",    description: "Branch on a condition",        icon: GitBranch, accent: "bg-rose-500/20 text-rose-400 border-rose-500/30" },
      { type: "switch_case",     label: "Switch / Case",   description: "Multi-way branch",             icon: Route,     accent: "bg-violet-500/20 text-violet-400 border-violet-500/30" },
      { type: "python_function", label: "Python Function", description: "Write custom Python code",    icon: Code2,     accent: "bg-fuchsia-500/20 text-fuchsia-400 border-fuchsia-500/30" },
    ],
  },
  {
    title: "Flow Control",
    items: [
      { type: "processor",       label: "Processor",       description: "Transform & relay data",       icon: Cpu,       accent: "bg-amber-500/20 text-amber-400 border-amber-500/30" },
      { type: "loop_foreach",    label: "Loop ForEach",    description: "4-handle loop iteration",      icon: Repeat,    accent: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30" },
      { type: "parallel_split",  label: "Parallel Split",  description: "Run children concurrently",    icon: GitFork,   accent: "bg-sky-500/20 text-sky-400 border-sky-500/30" },
      { type: "merge_join",      label: "Merge / Join",    description: "Merge parallel branches",      icon: Merge,     accent: "bg-teal-500/20 text-teal-400 border-teal-500/30" },
      { type: "delay",           label: "Delay",           description: "Pause for N seconds",          icon: Timer,     accent: "bg-orange-500/20 text-orange-400 border-orange-500/30" },
    ],
  },
  {
    title: "Output",
    items: [
      { type: "response_builder", label: "Response",       description: "Build API response",           icon: Send,      accent: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30" },
    ],
  },
  {
    title: "Middleware",
    items: [
      { type: "header_extractor", label: "Header Extract", description: "Extract request headers",      icon: FileSearch, accent: "bg-slate-500/20 text-slate-400 border-slate-500/30" },
      { type: "auth_node",        label: "Auth Gate",       description: "Validate API keys",            icon: ShieldCheck, accent: "bg-red-500/20 text-red-400 border-red-500/30" },
    ],
  },
];

// ── MiniMap color mapping ───────────────────────────────────────────
const MINIMAP_COLORS: Record<string, string> = {
  http_entry:       "#3b82f6",
  webhook_trigger:  "#ec4899",
  cron_trigger:     "#eab308",
  manual_trigger:   "#84cc16",
  if_condition:     "#f43f5e",
  switch_case:      "#8b5cf6",
  processor:        "#f59e0b",
  loop_foreach:     "#06b6d4",
  parallel_split:   "#0ea5e9",
  merge_join:       "#14b8a6",
  delay:            "#f97316",
  response_builder: "#10b981",
  header_extractor: "#64748b",
  auth_node:        "#ef4444",
  python_function:  "#d946ef",
};

// ── inner component (needs ReactFlowProvider above it) ─────────────
function FlowEditor({ fileId }: { fileId: string }) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [fileName, setFileName] = useState("Untitled");
  const [isSaving, setIsSaving] = useState(false);
  const [isDeploying, setIsDeploying] = useState(false);
  const [isStopping, setIsStopping] = useState(false);
  const [isLive, setIsLive] = useState(false);
  const [deployedPath, setDeployedPath] = useState<string | null>(null);
  const [deployedMethod, setDeployedMethod] = useState<string | null>(null);
  const [rfInstance, setRfInstance] = useState<ReactFlowInstance | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [overlayActive, setOverlayActive] = useState(false);
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const savedStylesRef = useRef<Map<string, any>>(new Map());
  const { getToken } = useAuth();
  const router = useRouter();

  const applyTraceOverlay = useCallback((trace: any[]) => {
    savedStylesRef.current = new Map();
    setNodes((nds) =>
      nds.map((node) => {
        savedStylesRef.current.set(node.id, node.style);
        const traceEntry = trace.find((t: any) => t.node_id === node.id);
        if (!traceEntry) return node;
        const glowColor = traceEntry.status === "success" ? "0 0 12px rgba(16,185,129,0.5)" : traceEntry.status === "failed" ? "0 0 12px rgba(239,68,68,0.5)" : "0 0 12px rgba(100,100,100,0.3)";
        return { ...node, style: { ...node.style, boxShadow: glowColor } };
      })
    );
    setOverlayActive(true);
    toast.success("Node overlay applied", { description: "Click 'Clear overlay' to restore" });
  }, [setNodes]);

  const clearOverlay = useCallback(() => {
    setNodes((nds) =>
      nds.map((node) => ({
        ...node,
        style: savedStylesRef.current.get(node.id) || {},
      }))
    );
    savedStylesRef.current.clear();
    setOverlayActive(false);
  }, [setNodes]);

  useEffect(() => {
    const load = async () => {
      try {
        const token = await getToken();
        const [graphRes, metaRes] = await Promise.all([
          axios.get(`http://localhost:8000/api/files/${fileId}`, {
            headers: { Authorization: `Bearer ${token}` },
          }),
          axios.get(`http://localhost:8000/api/files/${fileId}/meta`, {
            headers: { Authorization: `Bearer ${token}` },
          }),
        ]);
        setNodes(graphRes.data.nodes || []);
        setEdges(graphRes.data.edges || []);
        setFileName(metaRes.data.name || "Untitled");
        setIsLive(metaRes.data.is_deployed || false);
        setDeployedPath(metaRes.data.deployed_path || null);
        setDeployedMethod(metaRes.data.deployed_method || null);
      } catch {
        toast.error("Failed to load flow");
      }
    };
    load();
  }, [fileId]);

  const save = useCallback(async () => {
    setIsSaving(true);
    try {
      const token = await getToken();
      await axios.put(
        `http://localhost:8000/api/files/${fileId}`,
        { graph: { nodes, edges } },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success("Flow saved successfully");
    } catch {
      toast.error("Failed to save flow");
    } finally {
      setIsSaving(false);
    }
  }, [fileId, nodes, edges, getToken]);

  const deploy = useCallback(async () => {
    setIsDeploying(true);
    try {
      const token = await getToken();
      await axios.put(
        `http://localhost:8000/api/files/${fileId}`,
        { graph: { nodes, edges } },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      const res = await axios.post(
        `http://localhost:8000/api/files/deploy/${fileId}`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setIsLive(true);
      setDeployedPath(res.data.endpoint);
      setDeployedMethod(res.data.method);
      toast.success(
        `Deployed: ${res.data.method} ${res.data.endpoint}`,
        { description: "Your API endpoint is now live" }
      );
    } catch (err: any) {
      const status = err?.response?.status;
      const detail = err?.response?.data?.detail || err?.message || "Deploy failed";
      if (status === 422) {
        toast.error("Validation Error", {
          description: detail,
          duration: 8000,
        });
      } else {
        toast.error("Deployment failed", { description: detail });
      }
    } finally {
      setIsDeploying(false);
    }
  }, [fileId, nodes, edges, getToken]);

  const undeploy = useCallback(async () => {
    setIsStopping(true);
    try {
      const token = await getToken();
      await axios.post(
        `http://localhost:8000/api/files/undeploy/${fileId}`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setIsLive(false);
      setDeployedPath(null);
      setDeployedMethod(null);
      toast.success("Flow stopped", { description: "The API endpoint has been removed" });
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || "Stop failed";
      toast.error("Failed to stop", { description: msg });
    } finally {
      setIsStopping(false);
    }
  }, [fileId, getToken]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "s") {
        e.preventDefault();
        save();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [save]);

  const getInitialConfig = (type: string) => {
    switch (type) {
      case "http_entry":
        return { component: "http_entry", config: { is_entry: true, method: "POST", path: "/api/endpoint", request_schema: {}, response_schema: {} } };
      case "processor":
        return { component: "echo_processor", config: { label: "Echo Processor" } };
      case "response_builder":
        return { component: "response_builder", config: { is_response: true, response_schema: {}, field_mappings: [] } };
      case "if_condition":
        return { component: "if_condition", config: { field: "", operator: "==", value: "" } };
      case "switch_case":
        return { component: "switch_case", config: { field: "", cases: [] } };
      case "loop_foreach":
        return { component: "loop_foreach", config: { array_field: "items" } };
      case "parallel_split":
        return { component: "parallel_split", config: {} };
      case "merge_join":
        return { component: "merge_join", config: {} };
      case "delay":
        return { component: "delay", config: { seconds: 1 } };
      case "webhook_trigger":
        return { component: "webhook_trigger", config: { is_entry: true, method: "POST", path: "/webhook/endpoint" } };
      case "cron_trigger":
        return { component: "cron_trigger", config: { is_entry: true, cron_expression: "* * * * *" } };
      case "manual_trigger":
        return { component: "manual_trigger", config: { is_entry: true } };
      case "header_extractor":
        return { component: "header_extractor", config: { headers: [] } };
      case "auth_node":
        return { component: "auth_node", config: { type: "api_key", header_name: "x-api-key" } };
      case "python_function":
        return { component: "python_function", config: { code: "# data = merged upstream inputs (dict)\n# return a dict\nreturn {\"result\": data}" } };
      default:
        return { component: type, config: {} };
    }
  };

  const addNode = useCallback(
    (type: string) => {
      const offset = nodes.length;
      setNodes((nds) => [
        ...nds,
        {
          id: `${Date.now()}`,
          type,
          position: { x: 100 + offset * 400, y: 150 + (offset % 2) * 30 },
          data: getInitialConfig(type),
        },
      ]);
    },
    [nodes.length, setNodes]
  );

  const onConnect = useCallback(
    (conn: Connection) => {
      setEdges((eds) =>
        addEdge(
          { ...conn, animated: true, style: { stroke: "#6366f1", strokeWidth: 2 } },
          eds
        )
      );
    },
    [setEdges]
  );

  return (
    <div className="h-screen w-screen flex bg-[#0a0a0f] text-white overflow-hidden">
      {/* ── SIDEBAR ──────────────────────────────────────────────── */}
      <div className="w-64 border-r border-white/[0.06] bg-[#0d0d14] flex flex-col shrink-0 min-h-0">
        <div className="p-4 flex items-center gap-3 border-b border-white/[0.06]">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 text-white/50 hover:text-white hover:bg-white/10"
            onClick={() => router.back()}
          >
            <ArrowLeft className="w-4 h-4" />
          </Button>
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-indigo-400" />
            <span className="text-sm font-semibold text-white/80">Flow Editor</span>
          </div>
        </div>

        <ScrollArea className="flex-1 overflow-hidden px-4 pt-3">
          {PALETTE_SECTIONS.map((section, si) => (
            <div key={section.title} className={si > 0 ? "mt-1" : ""}>
              <div className="text-[10px] uppercase tracking-[0.2em] text-white/30 font-semibold mb-2 mt-2">
                {section.title}
              </div>
              <div className="space-y-1.5 mb-2">
                {section.items.map((item) => {
                  const Icon = item.icon;
                  return (
                    <button
                      key={item.type}
                      onClick={() => addNode(item.type)}
                      className="w-full group flex items-center gap-3 p-2.5 rounded-xl bg-white/[0.02] border border-white/[0.06] hover:border-white/[0.15] hover:bg-white/[0.05] transition-all duration-200"
                    >
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center border ${item.accent} transition-colors shrink-0`}>
                        <Icon className="w-3.5 h-3.5" />
                      </div>
                      <div className="text-left flex-1 min-w-0">
                        <div className="text-[11px] font-medium text-white/80 group-hover:text-white transition-colors truncate">
                          {item.label}
                        </div>
                        <div className="text-[9px] text-white/30 truncate">
                          {item.description}
                        </div>
                      </div>
                      <Grip className="w-3 h-3 text-white/10 group-hover:text-white/30 transition-colors shrink-0" />
                    </button>
                  );
                })}
              </div>
              {si < PALETTE_SECTIONS.length - 1 && (
                <Separator className="bg-white/[0.06] my-1.5" />
              )}
            </div>
          ))}

          <Separator className="bg-white/[0.06] my-2" />

          {/* info panel */}
          <div className="pb-4 space-y-2">
            <div className="text-[10px] uppercase tracking-[0.2em] text-white/30 font-semibold mb-2">
              Info
            </div>
            <div className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-3 space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="text-white/30">Nodes</span>
                <span className="text-white/60 font-mono">{nodes.length}</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-white/30">Edges</span>
                <span className="text-white/60 font-mono">{edges.length}</span>
              </div>
            </div>
            <div className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-3 space-y-2">
              <div className="text-[10px] text-white/25 leading-relaxed">
                <strong className="text-white/40">Tip:</strong> Connect a{" "}
                <span className="text-blue-400">Trigger</span> to{" "}
                <span className="text-amber-400">Logic/Processors</span> to a{" "}
                <span className="text-emerald-400">Response</span> to build a pipeline.
              </div>
              <div className="text-[10px] text-white/25 leading-relaxed">
                <strong className="text-white/40">Delete:</strong> Hover a node or click an edge and use the{" "}
                <span className="text-red-400">x</span> button.
              </div>
            </div>
          </div>
        </ScrollArea>
      </div>

      {/* ── MAIN AREA ────────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col">
        <div className="h-14 border-b border-white/[0.06] bg-[#0d0d14]/80 backdrop-blur-xl flex items-center px-4 gap-3 shrink-0">
          <div className="flex-1 flex items-center gap-3">
            <Badge variant="outline" className="bg-indigo-500/10 text-indigo-400 border-indigo-500/20 text-xs">
              {fileName}
            </Badge>
            {isLive ? (
              <Badge className="bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 text-[10px] gap-1.5 px-2">
                <Circle className="w-2 h-2 fill-emerald-400 animate-pulse" />
                Live
                {deployedPath && (
                  <span className="text-emerald-400/60 font-mono ml-1">
                    {deployedMethod} {deployedPath}
                  </span>
                )}
              </Badge>
            ) : (
              <Badge variant="outline" className="bg-white/5 text-white/30 border-white/10 text-[10px] gap-1.5 px-2">
                <Circle className="w-2 h-2 fill-white/20" />
                Stopped
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-2">
            {overlayActive && (
              <Button variant="ghost" size="sm" onClick={clearOverlay} className="text-amber-400/70 hover:text-amber-400 hover:bg-amber-500/10 gap-1.5 text-[10px] h-7 px-2">
                Clear overlay
              </Button>
            )}
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="ghost" size="sm" onClick={() => setDrawerOpen(true)} className="text-white/60 hover:text-white hover:bg-white/10 gap-2">
                  <ScrollText className="w-4 h-4" />
                  <span className="text-xs">Logs</span>
                </Button>
              </TooltipTrigger>
              <TooltipContent>View execution logs</TooltipContent>
            </Tooltip>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="ghost" size="sm" onClick={save} disabled={isSaving} className="text-white/60 hover:text-white hover:bg-white/10 gap-2">
                  {isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                  <span className="text-xs">Save</span>
                  <kbd className="hidden sm:inline text-[10px] text-white/20 bg-white/5 px-1.5 py-0.5 rounded font-mono">⌘S</kbd>
                </Button>
              </TooltipTrigger>
              <TooltipContent>Save flow (⌘S)</TooltipContent>
            </Tooltip>
            {isLive && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button size="sm" variant="ghost" onClick={undeploy} disabled={isStopping} className="text-red-400/70 hover:text-red-400 hover:bg-red-500/10 gap-2">
                    {isStopping ? <Loader2 className="w-4 h-4 animate-spin" /> : <Square className="w-3.5 h-3.5 fill-red-400/70" />}
                    <span className="text-xs">Stop</span>
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Remove deployed endpoint</TooltipContent>
              </Tooltip>
            )}
            <Tooltip>
              <TooltipTrigger asChild>
                <Button size="sm" onClick={deploy} disabled={isDeploying} className="bg-indigo-600 hover:bg-indigo-500 text-white gap-2">
                  {isDeploying ? <Loader2 className="w-4 h-4 animate-spin" /> : <Rocket className="w-4 h-4" />}
                  <span className="text-xs">{isLive ? "Redeploy" : "Deploy"}</span>
                </Button>
              </TooltipTrigger>
              <TooltipContent>{isLive ? "Save & redeploy" : "Save & deploy as live API"}</TooltipContent>
            </Tooltip>
          </div>
        </div>

        <div className="flex-1 relative" ref={reactFlowWrapper}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            nodeTypes={nodeTypes}
            edgeTypes={edgeTypes}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onInit={setRfInstance}
            deleteKeyCode={null}
            fitView
            style={rfStyle}
            defaultEdgeOptions={{
              type: "deletable",
              animated: true,
              style: { stroke: "#6366f1", strokeWidth: 2 },
            }}
            proOptions={{ hideAttribution: true }}
          >
            <Background variant={BackgroundVariant.Dots} gap={24} size={1} color="#ffffff08" />
            <Controls className="!bg-[#1a1a2e] !border-white/10 !rounded-xl !shadow-2xl [&>button]:!bg-[#1a1a2e] [&>button]:!border-white/10 [&>button]:!text-white/50 [&>button:hover]:!bg-white/10 [&>button:hover]:!text-white" />
            <MiniMap
              nodeColor={(n) => MINIMAP_COLORS[n.type || ""] || "#6366f1"}
              maskColor="rgba(0,0,0,0.85)"
              className="!bg-[#0d0d14] !border-white/[0.06] !rounded-xl"
              pannable
              zoomable
            />
          </ReactFlow>
        </div>
      </div>

      <ExecutionDrawer
        fileId={fileId}
        open={drawerOpen}
        onOpenChange={setDrawerOpen}
        onApplyOverlay={applyTraceOverlay}
      />
    </div>
  );
}

export default function FileEditorPage({
  params,
}: {
  params: Promise<{ fileId: string }>;
}) {
  const { fileId } = use(params);

  return (
    <ReactFlowProvider>
      <FlowEditor fileId={fileId} />
    </ReactFlowProvider>
  );
}
