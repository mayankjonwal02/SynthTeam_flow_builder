"use client";

import { useEffect, useState } from "react";
import axios from "axios";
import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { toast } from "sonner";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  Loader2,
  ChevronDown,
  ChevronRight,
  CheckCircle2,
  XCircle,
  SkipForward,
  ExternalLink,
  RefreshCw,
} from "lucide-react";

interface TraceEntry {
  node_id: string;
  node_name?: string;
  component: string;
  status: string;
  duration_ms: number;
  timestamp: string;
  input: any;
  output: any;
  error?: string;
}

interface ExecutionLog {
  id: string;
  execution_id: string;
  status: string;
  trace: TraceEntry[];
  created_at: string;
}

const STATUS_CONFIG: Record<string, { icon: any; color: string; bg: string; border: string }> = {
  success: { icon: CheckCircle2, color: "text-emerald-400", bg: "bg-emerald-500/10", border: "border-emerald-500/20" },
  failed:  { icon: XCircle,      color: "text-red-400",     bg: "bg-red-500/10",     border: "border-red-500/20" },
  skipped: { icon: SkipForward,  color: "text-white/30",    bg: "bg-white/5",        border: "border-white/10" },
};

function TraceNodeRow({ entry, isExpanded, onToggle }: { entry: TraceEntry; isExpanded: boolean; onToggle: () => void }) {
  const cfg = STATUS_CONFIG[entry.status] || STATUS_CONFIG.skipped;
  const StatusIcon = cfg.icon;

  return (
    <div className={`border rounded-lg overflow-hidden ${cfg.border}`}>
      <button onClick={onToggle} className="w-full flex items-center gap-2 px-3 py-2 hover:bg-white/[0.03] transition-colors">
        {isExpanded ? <ChevronDown className="w-3 h-3 text-white/30 shrink-0" /> : <ChevronRight className="w-3 h-3 text-white/30 shrink-0" />}
        <StatusIcon className={`w-3.5 h-3.5 ${cfg.color} shrink-0`} />
        <span className="text-[11px] text-white/70 font-mono truncate flex-1 text-left">{entry.node_name || entry.component}</span>
        <span className="text-[10px] text-white/30 font-mono shrink-0">{entry.duration_ms}ms</span>
      </button>
      {isExpanded && (
        <div className="px-3 pb-3 space-y-2 border-t border-white/[0.06]">
          <div className="pt-2 flex items-center gap-2 text-[10px] text-white/30">
            <span>Node: <span className="text-white/50 font-mono">{entry.node_id}</span></span>
            <span>|</span>
            <span>{new Date(entry.timestamp).toLocaleTimeString()}</span>
          </div>
          {entry.error && (
            <div className="bg-red-500/10 border border-red-500/20 rounded-md px-2.5 py-1.5">
              <span className="text-[10px] text-red-400 font-mono">{entry.error}</span>
            </div>
          )}
          <div>
            <div className="text-[9px] uppercase tracking-widest text-white/25 font-semibold mb-1">Input</div>
            <pre className="bg-black/30 rounded-md px-2.5 py-1.5 text-[10px] text-white/50 font-mono overflow-x-auto max-h-32 overflow-y-auto">
              {JSON.stringify(entry.input, null, 2) || "{}"}
            </pre>
          </div>
          <div>
            <div className="text-[9px] uppercase tracking-widest text-white/25 font-semibold mb-1">Output</div>
            <pre className="bg-black/30 rounded-md px-2.5 py-1.5 text-[10px] text-white/50 font-mono overflow-x-auto max-h-32 overflow-y-auto">
              {JSON.stringify(entry.output, null, 2) || "null"}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}

function ExecutionRow({ log, onApplyOverlay }: { log: ExecutionLog; onApplyOverlay?: (trace: TraceEntry[]) => void }) {
  const [expanded, setExpanded] = useState(false);
  const [expandedNodes, setExpandedNodes] = useState<Set<number>>(new Set());
  const cfg = STATUS_CONFIG[log.status] || STATUS_CONFIG.skipped;
  const StatusIcon = cfg.icon;

  const totalDuration = (log.trace || []).reduce((sum, t) => sum + (t.duration_ms || 0), 0);
  const nodeCount = (log.trace || []).length;
  const failCount = (log.trace || []).filter((t) => t.status === "failed").length;

  const toggleNode = (idx: number) => {
    setExpandedNodes((prev) => {
      const next = new Set(prev);
      next.has(idx) ? next.delete(idx) : next.add(idx);
      return next;
    });
  };

  return (
    <div className="space-y-2">
      <button onClick={() => setExpanded(!expanded)} className="w-full flex items-center gap-2.5 p-3 rounded-xl bg-white/[0.02] border border-white/[0.06] hover:border-white/[0.12] hover:bg-white/[0.04] transition-all">
        {expanded ? <ChevronDown className="w-3.5 h-3.5 text-white/30 shrink-0" /> : <ChevronRight className="w-3.5 h-3.5 text-white/30 shrink-0" />}
        <StatusIcon className={`w-4 h-4 ${cfg.color} shrink-0`} />
        <div className="flex-1 text-left min-w-0">
          <div className="text-[11px] text-white/70 font-mono truncate">
            {log.execution_id.slice(0, 8)}...
          </div>
          <div className="text-[9px] text-white/30 mt-0.5">
            {new Date(log.created_at).toLocaleString()}
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {failCount > 0 && (
            <Badge className="bg-red-500/15 text-red-400 border-red-500/25 text-[9px] px-1.5 py-0">{failCount} err</Badge>
          )}
          <Badge variant="outline" className={`text-[9px] px-1.5 py-0 ${cfg.bg} ${cfg.color} ${cfg.border}`}>
            {nodeCount} nodes
          </Badge>
          <span className="text-[10px] text-white/30 font-mono">{totalDuration.toFixed(1)}ms</span>
        </div>
      </button>

      {expanded && (
        <div className="ml-4 space-y-1.5">
          {onApplyOverlay && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onApplyOverlay(log.trace || [])}
              className="text-[10px] text-indigo-400 hover:text-indigo-300 hover:bg-indigo-500/10 h-7 px-2 mb-1"
            >
              Highlight nodes on canvas
            </Button>
          )}
          {(log.trace || []).map((entry, idx) => (
            <TraceNodeRow
              key={idx}
              entry={entry}
              isExpanded={expandedNodes.has(idx)}
              onToggle={() => toggleNode(idx)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default function ExecutionDrawer({
  fileId,
  open,
  onOpenChange,
  onApplyOverlay,
}: {
  fileId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onApplyOverlay?: (trace: TraceEntry[]) => void;
}) {
  const [logs, setLogs] = useState<ExecutionLog[]>([]);
  const [loading, setLoading] = useState(false);
  const { getToken } = useAuth();

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const token = await getToken();
      const res = await axios.get(
        `http://localhost:8000/api/files/${fileId}/logs?limit=15`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setLogs(res.data);
    } catch {
      toast.error("Failed to load execution logs");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (open) fetchLogs();
  }, [open]);

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side="right"
        showCloseButton
        className="!bg-[#0d0d14] !border-white/[0.06] !w-[420px] !max-w-[420px] !p-0 !gap-0 text-white"
      >
        <SheetHeader className="px-5 pt-5 pb-3 border-b border-white/[0.06]">
          <SheetTitle className="text-white text-base flex items-center gap-2">
            Execution Logs
            {logs.length > 0 && (
              <Badge variant="outline" className="bg-indigo-500/10 text-indigo-400 border-indigo-500/20 text-[10px] px-1.5 py-0">
                {logs.length}
              </Badge>
            )}
          </SheetTitle>
          <SheetDescription className="text-white/35 text-xs">
            Recent executions for this workflow.
          </SheetDescription>
        </SheetHeader>

        <div className="flex items-center justify-between px-5 py-2 border-b border-white/[0.06]">
          <Button variant="ghost" size="sm" onClick={fetchLogs} disabled={loading} className="text-white/40 hover:text-white hover:bg-white/10 h-7 px-2 text-[10px] gap-1">
            <RefreshCw className={`w-3 h-3 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Link href={`/files/${fileId}/logs`}>
            <Button variant="ghost" size="sm" className="text-indigo-400 hover:text-indigo-300 hover:bg-indigo-500/10 h-7 px-2 text-[10px] gap-1">
              View All
              <ExternalLink className="w-3 h-3" />
            </Button>
          </Link>
        </div>

        <ScrollArea className="flex-1 overflow-hidden">
          <div className="px-4 py-3 space-y-2">
            {loading ? (
              <div className="flex flex-col items-center justify-center py-16 gap-3">
                <Loader2 className="w-5 h-5 text-indigo-400 animate-spin" />
                <span className="text-xs text-white/30">Loading logs...</span>
              </div>
            ) : logs.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-16 gap-3 text-center">
                <CheckCircle2 className="w-8 h-8 text-white/10" />
                <p className="text-xs text-white/30">No executions yet.</p>
                <p className="text-[10px] text-white/20">Deploy and trigger your workflow to see logs here.</p>
              </div>
            ) : (
              logs.map((log) => (
                <ExecutionRow key={log.id} log={log} onApplyOverlay={onApplyOverlay} />
              ))
            )}
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
}
