"use client";

import { use, useEffect, useState, useCallback, useRef } from "react";
import axios from "axios";
import { API_URL } from "@/lib/api";
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
  Search,
  DatabaseZap,
  PenLine,
  Trash,
  TerminalSquare,
  PlayCircle,
  CheckCircle,
  RotateCcw,
  Sparkles,
  Bot,
  Users,
  Wand2,
  Eye,
  Mic,
  Volume2,
  Upload,
  BookOpen,
  Trash2,
  FileJson,
  Brain,
  Database,
  Calculator,
  Mail,
  MessageSquare,
  Workflow,
  Puzzle,
  FileText,
  FileUp,
  Scissors,
  Sparkle,
  X,
  PanelRightOpen,
  ChevronRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import ExecutionDrawer from "@/components/ExecutionDrawer";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import AICopilotPanel from "@/components/agent/AICopilotPanel";

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
  {
    title: "PostgreSQL",
    items: [
      { type: "pg_find",          label: "PG Find",         description: "Query Postgres rows",          icon: Search,        accent: "bg-blue-600/20 text-blue-400 border-blue-600/30" },
      { type: "pg_insert",        label: "PG Insert",       description: "Insert into Postgres",         icon: DatabaseZap,   accent: "bg-blue-600/20 text-blue-400 border-blue-600/30" },
      { type: "pg_update",        label: "PG Update",       description: "Update Postgres rows",         icon: PenLine,       accent: "bg-blue-600/20 text-blue-400 border-blue-600/30" },
      { type: "pg_delete",        label: "PG Delete",       description: "Delete Postgres rows",         icon: Trash,         accent: "bg-blue-600/20 text-blue-400 border-blue-600/30" },
      { type: "pg_raw_query",     label: "PG Query",        description: "Raw SQL on Postgres",          icon: TerminalSquare, accent: "bg-blue-600/20 text-blue-400 border-blue-600/30" },
      { type: "pg_txn_start",     label: "PG Txn Start",    description: "Begin PG transaction",         icon: PlayCircle,    accent: "bg-blue-600/20 text-blue-400 border-blue-600/30" },
      { type: "pg_txn_commit",    label: "PG Txn Commit",   description: "Commit PG transaction",        icon: CheckCircle,   accent: "bg-blue-600/20 text-blue-400 border-blue-600/30" },
      { type: "pg_txn_rollback",  label: "PG Txn Rollback", description: "Rollback PG transaction",      icon: RotateCcw,     accent: "bg-blue-600/20 text-blue-400 border-blue-600/30" },
    ],
  },
  {
    title: "MySQL",
    items: [
      { type: "mysql_find",          label: "MySQL Find",         description: "Query MySQL rows",          icon: Search,        accent: "bg-orange-600/20 text-orange-400 border-orange-600/30" },
      { type: "mysql_insert",        label: "MySQL Insert",       description: "Insert into MySQL",         icon: DatabaseZap,   accent: "bg-orange-600/20 text-orange-400 border-orange-600/30" },
      { type: "mysql_update",        label: "MySQL Update",       description: "Update MySQL rows",         icon: PenLine,       accent: "bg-orange-600/20 text-orange-400 border-orange-600/30" },
      { type: "mysql_delete",        label: "MySQL Delete",       description: "Delete MySQL rows",         icon: Trash,         accent: "bg-orange-600/20 text-orange-400 border-orange-600/30" },
      { type: "mysql_raw_query",     label: "MySQL Query",        description: "Raw SQL on MySQL",          icon: TerminalSquare, accent: "bg-orange-600/20 text-orange-400 border-orange-600/30" },
      { type: "mysql_txn_start",     label: "MySQL Txn Start",    description: "Begin MySQL transaction",   icon: PlayCircle,    accent: "bg-orange-600/20 text-orange-400 border-orange-600/30" },
      { type: "mysql_txn_commit",    label: "MySQL Txn Commit",   description: "Commit MySQL transaction",  icon: CheckCircle,   accent: "bg-orange-600/20 text-orange-400 border-orange-600/30" },
      { type: "mysql_txn_rollback",  label: "MySQL Txn Rollback", description: "Rollback MySQL transaction", icon: RotateCcw,    accent: "bg-orange-600/20 text-orange-400 border-orange-600/30" },
    ],
  },
  {
    title: "MongoDB",
    items: [
      { type: "mongo_find",       label: "Mongo Find",      description: "Find documents",               icon: Search,        accent: "bg-green-600/20 text-green-400 border-green-600/30" },
      { type: "mongo_insert",     label: "Mongo Insert",    description: "Insert document",              icon: DatabaseZap,   accent: "bg-green-600/20 text-green-400 border-green-600/30" },
      { type: "mongo_update",     label: "Mongo Update",    description: "Update documents",             icon: PenLine,       accent: "bg-green-600/20 text-green-400 border-green-600/30" },
      { type: "mongo_delete",     label: "Mongo Delete",    description: "Delete documents",             icon: Trash,         accent: "bg-green-600/20 text-green-400 border-green-600/30" },
      { type: "mongo_aggregate",  label: "Mongo Aggregate", description: "Aggregation pipeline",         icon: TerminalSquare, accent: "bg-green-600/20 text-green-400 border-green-600/30" },
    ],
  },
  {
    title: "SQLite",
    items: [
      { type: "sqlite_find",      label: "SQLite Find",     description: "Query SQLite rows",            icon: Search,        accent: "bg-amber-600/20 text-amber-400 border-amber-600/30" },
      { type: "sqlite_insert",    label: "SQLite Insert",   description: "Insert into SQLite",           icon: DatabaseZap,   accent: "bg-amber-600/20 text-amber-400 border-amber-600/30" },
      { type: "sqlite_update",    label: "SQLite Update",   description: "Update SQLite rows",           icon: PenLine,       accent: "bg-amber-600/20 text-amber-400 border-amber-600/30" },
      { type: "sqlite_delete",    label: "SQLite Delete",   description: "Delete SQLite rows",           icon: Trash,         accent: "bg-amber-600/20 text-amber-400 border-amber-600/30" },
      { type: "sqlite_raw_query", label: "SQLite Query",    description: "Raw SQL on SQLite",            icon: TerminalSquare, accent: "bg-amber-600/20 text-amber-400 border-amber-600/30" },
    ],
  },
  {
    title: "Supabase",
    items: [
      { type: "supa_find",        label: "Supa Find",       description: "Query Supabase rows",          icon: Search,        accent: "bg-emerald-600/20 text-emerald-400 border-emerald-600/30" },
      { type: "supa_insert",      label: "Supa Insert",     description: "Insert into Supabase",         icon: DatabaseZap,   accent: "bg-emerald-600/20 text-emerald-400 border-emerald-600/30" },
      { type: "supa_update",      label: "Supa Update",     description: "Update Supabase rows",         icon: PenLine,       accent: "bg-emerald-600/20 text-emerald-400 border-emerald-600/30" },
      { type: "supa_delete",      label: "Supa Delete",     description: "Delete Supabase rows",         icon: Trash,         accent: "bg-emerald-600/20 text-emerald-400 border-emerald-600/30" },
      { type: "supa_raw_query",   label: "Supa Query",      description: "Raw SQL on Supabase",          icon: TerminalSquare, accent: "bg-emerald-600/20 text-emerald-400 border-emerald-600/30" },
    ],
  },
  {
    title: "AI Config",
    items: [
      { type: "llm_model",            label: "LLM Model",         description: "Configure LLM provider & model", icon: Cpu,      accent: "bg-purple-500/20 text-purple-400 border-purple-500/30" },
      { type: "output_structure",      label: "Output Structure",  description: "JSON schema for structured output", icon: FileJson, accent: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30" },
      { type: "memory_config",         label: "Memory",            description: "Agent memory backend config",   icon: Brain,     accent: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30" },
      { type: "embedding_model",       label: "Embedding Model",   description: "Configure embedding provider",  icon: Layers,    accent: "bg-indigo-500/20 text-indigo-400 border-indigo-500/30" },
      { type: "vectorstore_config",    label: "Vector Store",      description: "Configure vector DB connection", icon: Database,  accent: "bg-violet-500/20 text-violet-400 border-violet-500/30" },
    ],
  },
  {
    title: "AI Tools",
    items: [
      { type: "tool_web_search",      label: "Web Search",        description: "Tavily web search tool",        icon: Globe,     accent: "bg-amber-500/20 text-amber-400 border-amber-500/30" },
      { type: "tool_http_request",     label: "HTTP Request",      description: "HTTP call tool for agents",     icon: Send,      accent: "bg-amber-500/20 text-amber-400 border-amber-500/30" },
      { type: "tool_calculator",       label: "Calculator",        description: "Math evaluation tool",          icon: Calculator, accent: "bg-amber-500/20 text-amber-400 border-amber-500/30" },
      { type: "tool_db_query",         label: "DB Query",          description: "Database query tool",           icon: DatabaseZap, accent: "bg-amber-500/20 text-amber-400 border-amber-500/30" },
      { type: "tool_code_executor",    label: "Code Executor",     description: "Sandboxed Python tool",         icon: Code2,     accent: "bg-amber-500/20 text-amber-400 border-amber-500/30" },
      { type: "tool_file_ops",         label: "File Ops",          description: "File read/write tool",          icon: FileText,  accent: "bg-amber-500/20 text-amber-400 border-amber-500/30" },
      { type: "tool_email",            label: "Email Sender",      description: "SMTP email tool",               icon: Mail,      accent: "bg-amber-500/20 text-amber-400 border-amber-500/30" },
      { type: "tool_gmail",            label: "Gmail",             description: "Send email via Gmail SMTP",    icon: Mail,      accent: "bg-red-500/20 text-red-400 border-red-500/30" },
      { type: "tool_slack",            label: "Slack Notifier",    description: "Slack webhook tool",            icon: MessageSquare, accent: "bg-amber-500/20 text-amber-400 border-amber-500/30" },
      { type: "tool_workflow",         label: "Workflow Invoker",  description: "Call other workflows",          icon: Workflow,  accent: "bg-amber-500/20 text-amber-400 border-amber-500/30" },
      { type: "tool_composio",         label: "Composio",          description: "Composio actions integration",  icon: Puzzle,    accent: "bg-amber-500/20 text-amber-400 border-amber-500/30" },
      { type: "tool_knowledge_base",   label: "Knowledge Base",    description: "RAG retrieval tool for agents", icon: BookOpen,  accent: "bg-amber-500/20 text-amber-400 border-amber-500/30" },
    ],
  },
  {
    title: "AI / LLM",
    items: [
      { type: "llm_call",             label: "LLM Call",          description: "Multi-provider LLM invocation", icon: Sparkles,  accent: "bg-purple-500/20 text-purple-400 border-purple-500/30" },
    ],
  },
  {
    title: "RAG Pipeline",
    items: [
      { type: "doc_loader",           label: "Document Loader",   description: "Load text from URL/file/raw",   icon: FileUp,    accent: "bg-teal-500/20 text-teal-400 border-teal-500/30" },
      { type: "text_splitter",        label: "Text Splitter",     description: "Chunk documents for embedding", icon: Scissors,  accent: "bg-teal-500/20 text-teal-400 border-teal-500/30" },
      { type: "embedding_generate",   label: "Embedding",         description: "Generate text embeddings",      icon: Layers,    accent: "bg-indigo-500/20 text-indigo-400 border-indigo-500/30" },
      { type: "vector_upsert",        label: "Vector Upsert",     description: "Insert into vector DB",         icon: Upload,    accent: "bg-indigo-500/20 text-indigo-400 border-indigo-500/30" },
      { type: "vector_search",        label: "Vector Search",     description: "Similarity search",             icon: Search,    accent: "bg-indigo-500/20 text-indigo-400 border-indigo-500/30" },
      { type: "vector_delete",        label: "Vector Delete",     description: "Delete from vector DB",         icon: Trash2,    accent: "bg-indigo-500/20 text-indigo-400 border-indigo-500/30" },
      { type: "retrieval",            label: "RAG Retrieval",     description: "Embed + search + return context", icon: BookOpen, accent: "bg-indigo-500/20 text-indigo-400 border-indigo-500/30" },
    ],
  },
  {
    title: "Agents",
    items: [
      { type: "agent_run",            label: "Agent (ReAct)",     description: "ReAct agent with tools",        icon: Bot,       accent: "bg-pink-500/20 text-pink-400 border-pink-500/30" },
      { type: "autonomous_agent",     label: "Autonomous Agent",  description: "Plans & executes autonomously", icon: Wand2,     accent: "bg-pink-500/20 text-pink-400 border-pink-500/30" },
    ],
  },
  {
    title: "Vision & Speech",
    items: [
      { type: "vision_analyze",       label: "Vision Analyze",    description: "Analyze images with AI",        icon: Eye,       accent: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30" },
      { type: "speech_to_text",       label: "Speech to Text",    description: "Transcribe audio to text",      icon: Mic,       accent: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30" },
      { type: "text_to_speech",       label: "Text to Speech",    description: "Convert text to audio",         icon: Volume2,   accent: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30" },
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
  python_function:    "#d946ef",
  pg_find:            "#2563eb", pg_insert: "#2563eb", pg_update: "#2563eb", pg_delete: "#2563eb",
  pg_raw_query:       "#2563eb", pg_txn_start: "#2563eb", pg_txn_commit: "#2563eb", pg_txn_rollback: "#2563eb",
  mysql_find:         "#ea580c", mysql_insert: "#ea580c", mysql_update: "#ea580c", mysql_delete: "#ea580c",
  mysql_raw_query:    "#ea580c", mysql_txn_start: "#ea580c", mysql_txn_commit: "#ea580c", mysql_txn_rollback: "#ea580c",
  mongo_find:         "#16a34a", mongo_insert: "#16a34a", mongo_update: "#16a34a", mongo_delete: "#16a34a",
  mongo_aggregate:    "#16a34a",
  sqlite_find:        "#d97706", sqlite_insert: "#d97706", sqlite_update: "#d97706", sqlite_delete: "#d97706",
  sqlite_raw_query:   "#d97706",
  supa_find:          "#059669", supa_insert: "#059669", supa_update: "#059669", supa_delete: "#059669",
  supa_raw_query:     "#059669",
  // AI Config
  llm_model: "#a855f7", output_structure: "#10b981", memory_config: "#06b6d4",
  embedding_model: "#6366f1", vectorstore_config: "#8b5cf6",
  // AI Tools
  tool_web_search: "#f59e0b", tool_http_request: "#f59e0b", tool_calculator: "#f59e0b",
  tool_db_query: "#f59e0b", tool_code_executor: "#f59e0b", tool_file_ops: "#f59e0b",
  tool_email: "#f59e0b", tool_gmail: "#ef4444", tool_slack: "#f59e0b", tool_workflow: "#f59e0b",
  tool_composio: "#f59e0b", tool_knowledge_base: "#f59e0b",
  // RAG Pipeline
  doc_loader: "#14b8a6", text_splitter: "#14b8a6",
  // AI Execution
  llm_call: "#a855f7",
  embedding_generate: "#6366f1", vector_upsert: "#6366f1", vector_search: "#6366f1", vector_delete: "#6366f1",
  retrieval: "#6366f1",
  agent_run: "#ec4899", autonomous_agent: "#ec4899",
  vision_analyze: "#06b6d4", speech_to_text: "#06b6d4", text_to_speech: "#06b6d4",
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
  const [copilotOpen, setCopilotOpen] = useState(false);
  const [overlayActive, setOverlayActive] = useState(false);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(["Triggers"]));
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const savedStylesRef = useRef<Map<string, any>>(new Map());
  const { getToken, isLoaded: authLoaded } = useAuth();
  const router = useRouter();
  // Saving before the graph has loaded would overwrite the stored flow with an empty one
  const [loadState, setLoadState] = useState<"loading" | "loaded" | "error">("loading");

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
    if (!authLoaded) return;
    const load = async () => {
      setLoadState("loading");
      try {
        const token = await getToken();
        const [graphRes, metaRes] = await Promise.all([
          axios.get(`${API_URL}/api/files/${fileId}`, {
            headers: { Authorization: `Bearer ${token}` },
          }),
          axios.get(`${API_URL}/api/files/${fileId}/meta`, {
            headers: { Authorization: `Bearer ${token}` },
          }),
        ]);
        setNodes(graphRes.data.nodes || []);
        setEdges(graphRes.data.edges || []);
        setFileName(metaRes.data.name || "Untitled");
        setIsLive(metaRes.data.is_deployed || false);
        setDeployedPath(metaRes.data.deployed_path || null);
        setDeployedMethod(metaRes.data.deployed_method || null);
        setLoadState("loaded");
      } catch {
        setLoadState("error");
        toast.error("Failed to load flow", {
          description: "Saving is disabled so the stored flow isn't overwritten. Reload to try again.",
        });
      }
    };
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fileId, authLoaded]);

  /** Graph as it should be stored: without the temporary trace-overlay styling. */
  const graphForSave = useCallback(() => {
    const saved = savedStylesRef.current;
    const cleanNodes = overlayActive
      ? nodes.map((n) => ({ ...n, style: saved.get(n.id) ?? {} }))
      : nodes;
    return { nodes: cleanNodes, edges };
  }, [nodes, edges, overlayActive]);

  const ensureLoaded = useCallback(() => {
    if (loadState === "loaded") return true;
    toast.error(
      loadState === "loading" ? "The flow is still loading" : "The flow failed to load, so it can't be saved",
    );
    return false;
  }, [loadState]);

  const save = useCallback(async () => {
    if (!ensureLoaded()) return;
    setIsSaving(true);
    try {
      const token = await getToken();
      await axios.put(
        `${API_URL}/api/files/${fileId}`,
        { graph: graphForSave() },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success("Flow saved successfully");
    } catch {
      toast.error("Failed to save flow");
    } finally {
      setIsSaving(false);
    }
  }, [fileId, getToken, graphForSave, ensureLoaded]);

  const deploy = useCallback(async () => {
    if (!ensureLoaded()) return;
    setIsDeploying(true);
    try {
      const token = await getToken();
      await axios.put(
        `${API_URL}/api/files/${fileId}`,
        { graph: graphForSave() },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      const res = await axios.post(
        `${API_URL}/api/files/deploy/${fileId}`,
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
      if (status === 422 || status === 409) {
        toast.error(status === 409 ? "Endpoint already in use" : "Validation Error", {
          description: detail,
          duration: 8000,
        });
      } else {
        toast.error("Deployment failed", { description: detail });
      }
    } finally {
      setIsDeploying(false);
    }
  }, [fileId, getToken, graphForSave, ensureLoaded]);

  const undeploy = useCallback(async () => {
    const endpoint = deployedPath ? `${deployedMethod ?? ""} ${deployedPath}`.trim() : "this endpoint";
    if (!window.confirm(`Stop ${endpoint}? Callers will get 404 until you deploy again.`)) return;
    setIsStopping(true);
    try {
      const token = await getToken();
      await axios.post(
        `${API_URL}/api/files/undeploy/${fileId}`,
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
  }, [fileId, getToken, deployedPath, deployedMethod]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "s") {
        e.preventDefault();
        if (!isSaving) save();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [save, isSaving]);

  const getInitialConfig = (type: string) => {
    switch (type) {
      case "http_entry":
        return { component: "http_entry", config: { is_entry: true, method: "POST", path: "/api/endpoint", request_schema: {}, response_schema: {} } };
      case "processor":
        return { component: "echo_processor", config: { label: "Echo Processor", field_mappings: [] } };
      case "response_builder":
        return { component: "response_builder", config: { is_response: true, response_schema: {}, field_mappings: [] } };
      case "if_condition":
        return { component: "if_condition", config: { field: "", field_mode: "expression", operator: "==", value: "", value_mode: "static" } };
      case "switch_case":
        return { component: "switch_case", config: { field: "", field_mode: "expression", cases: [] } };
      case "loop_foreach":
        return { component: "loop_foreach", config: { array_field: "items", array_field_mode: "expression" } };
      case "parallel_split":
        return { component: "parallel_split", config: {} };
      case "merge_join":
        return { component: "merge_join", config: {} };
      case "delay":
        return { component: "delay", config: { seconds: "1", seconds_mode: "static" } };
      case "webhook_trigger":
        return { component: "webhook_trigger", config: { is_entry: true, method: "POST", path: "/webhook/endpoint" } };
      case "cron_trigger":
        return { component: "cron_trigger", config: { is_entry: true, cron_expression: "* * * * *" } };
      case "manual_trigger":
        return { component: "manual_trigger", config: { is_entry: true } };
      case "header_extractor":
        return { component: "header_extractor", config: { headers: [], header_mappings: [] } };
      case "auth_node":
        return { component: "auth_node", config: { type: "api_key", header_name: "x-api-key", header_name_mode: "static" } };
      case "python_function":
        return { component: "python_function", config: { code: "# data = merged upstream inputs (dict)\n# return a dict\nreturn {\"result\": data}" } };
      case "pg_find": case "mysql_find": case "sqlite_find": case "supa_find":
        return { component: type, config: { connection_id: "", table: "", filter_mappings: [] } };
      case "pg_insert": case "mysql_insert": case "sqlite_insert": case "supa_insert":
        return { component: type, config: { connection_id: "", table: "" } };
      case "pg_update": case "mysql_update": case "sqlite_update": case "supa_update":
        return { component: type, config: { connection_id: "", table: "", filter_mappings: [] } };
      case "pg_delete": case "mysql_delete": case "sqlite_delete": case "supa_delete":
        return { component: type, config: { connection_id: "", table: "", filter_mappings: [] } };
      case "pg_raw_query": case "mysql_raw_query": case "sqlite_raw_query": case "supa_raw_query":
        return { component: type, config: { connection_id: "", query: "" } };
      case "pg_txn_start": case "mysql_txn_start":
        return { component: type, config: { connection_id: "" } };
      case "pg_txn_commit": case "mysql_txn_commit":
        return { component: type, config: {} };
      case "pg_txn_rollback": case "mysql_txn_rollback":
        return { component: type, config: {} };
      case "mongo_find":
        return { component: "mongo_find", config: { connection_id: "", database: "", collection: "", filter_mappings: [] } };
      case "mongo_insert":
        return { component: "mongo_insert", config: { connection_id: "", database: "", collection: "" } };
      case "mongo_update":
        return { component: "mongo_update", config: { connection_id: "", database: "", collection: "", filter_mappings: [] } };
      case "mongo_delete":
        return { component: "mongo_delete", config: { connection_id: "", database: "", collection: "", filter_mappings: [] } };
      case "mongo_aggregate":
        return { component: "mongo_aggregate", config: { connection_id: "", database: "", collection: "", pipeline: "[]" } };
      // AI Config nodes
      case "llm_model":
        return { component: "llm_model", config: { provider: "openai", model: "gpt-4o-mini", api_key: "", temperature: "0.7" } };
      case "output_structure":
        return { component: "output_structure", config: { schema: "" } };
      case "memory_config":
        return { component: "memory_config", config: { backend: "in_memory", session_id: "default", max_messages: "50" } };
      case "embedding_model":
        return { component: "embedding_model", config: { provider: "openai", model: "", api_key: "" } };
      case "vectorstore_config":
        return { component: "vectorstore_config", config: { provider: "qdrant", collection: "default", url: "", api_key: "" } };
      // AI Tool nodes
      case "tool_web_search":
        return { component: "tool_web_search", config: { api_key: "", max_results: "5" } };
      case "tool_http_request":
        return { component: "tool_http_request", config: { allowed_methods: "GET,POST", timeout: "30" } };
      case "tool_calculator":
        return { component: "tool_calculator", config: {} };
      case "tool_db_query":
        return { component: "tool_db_query", config: { db_type: "postgres", connection_id: "" } };
      case "tool_code_executor":
        return { component: "tool_code_executor", config: { timeout: "10" } };
      case "tool_file_ops":
        return { component: "tool_file_ops", config: { mode: "read", base_path: "/tmp" } };
      case "tool_email":
        return { component: "tool_email", config: { smtp_host: "", smtp_port: "587", username: "", password: "", from_email: "" } };
      case "tool_gmail":
        return { component: "tool_gmail", config: { email: "", app_password: "" } };
      case "tool_slack":
        return { component: "tool_slack", config: { webhook_url: "" } };
      case "tool_workflow":
        return { component: "tool_workflow", config: { workflow_url: "", method: "POST" } };
      case "tool_composio":
        return { component: "tool_composio", config: { api_key: "", action: "" } };
      case "tool_knowledge_base":
        return { component: "tool_knowledge_base", config: { data_description: "", collection: "default", top_k: "5", embedding_provider: "openai", embedding_model: "", embedding_api_key: "", vectorstore_provider: "qdrant", vectorstore_url: "", vectorstore_api_key: "" } };
      // RAG pipeline nodes
      case "doc_loader":
        return { component: "doc_loader", config: { source_type: "text", text: "", url: "", file_path: "" } };
      case "text_splitter":
        return { component: "text_splitter", config: { strategy: "character", chunk_size: "1000", overlap: "200" } };
      // AI Execution nodes
      case "llm_call":
        return { component: "llm_call", config: { system_prompt: "", system_prompt_source: "static", prompt_template: "{{input}}", prompt_template_source: "static" } };
      case "embedding_generate":
        return { component: "embedding_generate", config: { text_template: "{{input}}" } };
      case "vector_upsert":
        return { component: "vector_upsert", config: {} };
      case "vector_search":
        return { component: "vector_search", config: { top_k: "5" } };
      case "vector_delete":
        return { component: "vector_delete", config: {} };
      case "retrieval":
        return { component: "retrieval", config: { top_k: "5" } };
      case "agent_run":
        return { component: "agent_run", config: { system_prompt: "", system_prompt_source: "static", prompt_template: "{{input}}", prompt_template_source: "static", max_iterations: "10" } };
      case "autonomous_agent":
        return { component: "autonomous_agent", config: { system_prompt: "", system_prompt_source: "static", goal: "{{input}}", goal_source: "static", max_iterations: "10" } };
      case "vision_analyze":
        return { component: "vision_analyze", config: { image_url: "", prompt: "Describe this image." } };
      case "speech_to_text":
        return { component: "speech_to_text", config: { provider: "openai_whisper", audio_path: "" } };
      case "text_to_speech":
        return { component: "text_to_speech", config: { provider: "openai", voice: "alloy", text_template: "{{input}}" } };
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

  const CONFIG_TOOL_SUBAGENT_TYPES = new Set([
    "llm_model", "output_structure", "memory_config", "embedding_model", "vectorstore_config",
    "tool_web_search", "tool_http_request", "tool_calculator", "tool_db_query", "tool_code_executor",
    "tool_file_ops", "tool_email", "tool_gmail", "tool_slack", "tool_workflow", "tool_composio", "tool_knowledge_base",
    "agent_run", "autonomous_agent",
  ]);

  const onConnect = useCallback(
    (conn: Connection) => {
      const sourceNode = nodes.find((n: any) => n.id === conn.source);
      const sourceType = sourceNode?.type || "";
      let targetHandle = conn.targetHandle || "";

      if (targetHandle.startsWith("ai_")) {
        const expectedBySource: Record<string, string> = {
          llm_model: "ai_model",
          output_structure: "ai_structure",
          memory_config: "ai_memory",
          embedding_model: "ai_embedding",
          vectorstore_config: "ai_vectorstore",
          tool_web_search: "ai_tool",
          tool_http_request: "ai_tool",
          tool_calculator: "ai_tool",
          tool_db_query: "ai_tool",
          tool_code_executor: "ai_tool",
          tool_file_ops: "ai_tool",
          tool_email: "ai_tool",
          tool_gmail: "ai_tool",
          tool_slack: "ai_tool",
          tool_workflow: "ai_tool",
          tool_composio: "ai_tool",
          tool_knowledge_base: "ai_tool",
          agent_run: "ai_subagent",
          autonomous_agent: "ai_subagent",
        };
        if (CONFIG_TOOL_SUBAGENT_TYPES.has(sourceType)) {
          const expected = expectedBySource[sourceType];
          if (!expected || expected !== targetHandle) {
            toast.error("Invalid connection", {
              description: "Connect config/tool nodes to the matching handle (Model, Tools, Memory, etc.).",
            });
            return;
          }
        } else {
          targetHandle = "input";
        }
      }

      const finalConn = { ...conn, targetHandle: targetHandle || conn.targetHandle };

      setEdges((eds) =>
        addEdge(
          { ...finalConn, animated: true, style: { stroke: "#6366f1", strokeWidth: 2 } },
          eds
        )
      );
    },
    [nodes, setEdges]
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

        <ScrollArea className="flex-1 min-h-0 px-3 pt-2">
          <div className="space-y-0.5 pb-2">
            {PALETTE_SECTIONS.map((section) => {
              const isExpanded = expandedSections.has(section.title);
              return (
                <div key={section.title}>
                  <button
                    onClick={() =>
                      setExpandedSections((prev) => {
                        const next = new Set(prev);
                        if (next.has(section.title)) next.delete(section.title);
                        else next.add(section.title);
                        return next;
                      })
                    }
                    className="w-full flex items-center gap-2 px-2 py-2 rounded-lg hover:bg-white/[0.04] transition-colors group"
                  >
                    <ChevronRight
                      className={`w-3.5 h-3.5 text-white/30 group-hover:text-white/50 transition-transform duration-200 shrink-0 ${
                        isExpanded ? "rotate-90" : ""
                      }`}
                    />
                    <span className="text-[11px] uppercase tracking-[0.15em] text-white/40 group-hover:text-white/60 font-semibold transition-colors">
                      {section.title}
                    </span>
                    <span className="ml-auto text-[10px] text-white/20 font-mono tabular-nums">
                      {section.items.length}
                    </span>
                  </button>

                  {isExpanded && (
                    <div className="space-y-1 pl-2 pr-1 pb-1.5 pt-0.5">
                      {section.items.map((item) => {
                        const Icon = item.icon;
                        return (
                          <button
                            key={item.type}
                            onClick={() => addNode(item.type)}
                            className="w-full group flex items-center gap-2.5 p-2 rounded-lg bg-white/[0.02] border border-white/[0.04] hover:border-white/[0.15] hover:bg-white/[0.05] transition-all duration-200"
                          >
                            <div
                              className={`w-7 h-7 rounded-md flex items-center justify-center border ${item.accent} transition-colors shrink-0`}
                            >
                              <Icon className="w-3.5 h-3.5" />
                            </div>
                            <div className="text-left flex-1 min-w-0">
                              <div className="text-[11px] font-medium text-white/80 group-hover:text-white transition-colors truncate">
                                {item.label}
                              </div>
                              <div className="text-[9px] text-white/30 truncate leading-tight">
                                {item.description}
                              </div>
                            </div>
                            <Grip className="w-3 h-3 text-white/10 group-hover:text-white/30 transition-colors shrink-0" />
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </ScrollArea>

        {/* Info panel — fixed at bottom so nodes/edges count is always visible */}
        <div className="shrink-0 border-t border-white/[0.06] bg-[#0d0d14] px-4 py-3 space-y-2">
          <div className="text-[10px] uppercase tracking-[0.2em] text-white/40 font-semibold">
            Graph
          </div>
          <div className="bg-white/[0.06] border border-white/[0.1] rounded-xl p-3 space-y-2">
            <div className="flex justify-between items-center text-sm">
              <span className="text-white/60">Nodes</span>
              <span className="text-white font-mono font-medium tabular-nums">{nodes.length}</span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-white/60">Edges</span>
              <span className="text-white font-mono font-medium tabular-nums">{edges.length}</span>
            </div>
          </div>
          <div className="bg-white/[0.04] border border-white/[0.08] rounded-xl p-2.5 space-y-1.5">
            <div className="text-[10px] text-white/50 leading-relaxed">
              <strong className="text-white/70">Tip:</strong> Connect a{" "}
              <span className="text-blue-400">Trigger</span> →{" "}
              <span className="text-amber-400">Processors</span> →{" "}
              <span className="text-emerald-400">Response</span>.
            </div>
            <div className="text-[10px] text-white/50 leading-relaxed">
              <strong className="text-white/70">Delete:</strong> Hover node or edge and click{" "}
              <span className="text-red-400">×</span>.
            </div>
          </div>
        </div>
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
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setCopilotOpen((p) => !p)}
                  className={`gap-2 ${copilotOpen ? "text-purple-400 bg-purple-500/10 hover:bg-purple-500/20" : "text-white/60 hover:text-white hover:bg-white/10"}`}
                >
                  <Sparkle className="w-4 h-4" />
                  <span className="text-xs">AI Copilot</span>
                </Button>
              </TooltipTrigger>
              <TooltipContent>AI assistant to help build your workflow</TooltipContent>
            </Tooltip>
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

        <div className="flex-1 flex min-h-0">
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

          {copilotOpen && (
            <div className="w-[380px] border-l border-white/[0.06] shrink-0">
              <AICopilotPanel
                nodes={nodes}
                edges={edges}
                setNodes={setNodes}
                setEdges={setEdges}
                onClose={() => setCopilotOpen(false)}
              />
            </div>
          )}
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
