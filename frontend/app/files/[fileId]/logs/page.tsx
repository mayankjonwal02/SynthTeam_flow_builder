"use client";

import { use, useEffect, useState, useCallback } from "react";
import axios from "axios";
import { API_URL, apiErrorMessage } from "@/lib/api";
import { useAuth } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import Navbar from "@/components/Navbar";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  ArrowLeft,
  Loader2,
  CheckCircle2,
  XCircle,
  SkipForward,
  ChevronDown,
  ChevronRight,
  RefreshCw,
  ScrollText,
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

const STATUS_ICON: Record<string, any> = {
  success: CheckCircle2,
  failed:  XCircle,
  rejected: XCircle,
  skipped: SkipForward,
};

const STATUS_STYLE: Record<string, { color: string; bg: string; border: string }> = {
  success: { color: "text-emerald-400", bg: "bg-emerald-500/10", border: "border-emerald-500/20" },
  failed:  { color: "text-red-400",     bg: "bg-red-500/10",     border: "border-red-500/20" },
  rejected: { color: "text-amber-400",  bg: "bg-amber-500/10",   border: "border-amber-500/20" },
  skipped: { color: "text-white/30",    bg: "bg-white/5",        border: "border-white/10" },
};

function TraceNodeDetail({ entry }: { entry: TraceEntry }) {
  const [expanded, setExpanded] = useState(false);
  const s = STATUS_STYLE[entry.status] || STATUS_STYLE.skipped;
  const Icon = STATUS_ICON[entry.status] || SkipForward;

  return (
    <div className={`border rounded-lg overflow-hidden ${s.border}`}>
      <button onClick={() => setExpanded(!expanded)} className="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-white/[0.03] transition-colors">
        {expanded ? <ChevronDown className="w-3.5 h-3.5 text-white/30 shrink-0" /> : <ChevronRight className="w-3.5 h-3.5 text-white/30 shrink-0" />}
        <Icon className={`w-4 h-4 ${s.color} shrink-0`} />
        <span className="text-xs text-white/70 font-mono truncate flex-1 text-left">{entry.node_name || entry.component}</span>
        <span className="text-[10px] text-white/40 font-mono shrink-0">id: {entry.node_id}</span>
        <Badge variant="outline" className={`text-[9px] px-1.5 py-0 ${s.bg} ${s.color} ${s.border}`}>{entry.status}</Badge>
        <span className="text-[10px] text-white/30 font-mono shrink-0 w-16 text-right">{entry.duration_ms}ms</span>
      </button>
      {expanded && (
        <div className="px-4 pb-4 space-y-3 border-t border-white/[0.06] pt-3">
          <div className="text-[10px] text-white/30">
            Timestamp: <span className="text-white/50 font-mono">{new Date(entry.timestamp).toLocaleString()}</span>
          </div>
          {entry.error && (
            <div className="bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
              <div className="text-[9px] uppercase tracking-widest text-red-400/60 font-semibold mb-1">Error</div>
              <pre className="text-[11px] text-red-400 font-mono whitespace-pre-wrap">{entry.error}</pre>
            </div>
          )}
          <div>
            <div className="text-[9px] uppercase tracking-widest text-white/25 font-semibold mb-1.5">Input</div>
            <pre className="bg-black/30 rounded-lg px-3 py-2 text-[11px] text-white/50 font-mono overflow-x-auto max-h-48 overflow-y-auto">
              {JSON.stringify(entry.input, null, 2) || "{}"}
            </pre>
          </div>
          <div>
            <div className="text-[9px] uppercase tracking-widest text-white/25 font-semibold mb-1.5">Output</div>
            <pre className="bg-black/30 rounded-lg px-3 py-2 text-[11px] text-white/50 font-mono overflow-x-auto max-h-48 overflow-y-auto">
              {JSON.stringify(entry.output, null, 2) || "null"}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}

function ExecutionLogRow({ log }: { log: ExecutionLog }) {
  const [expanded, setExpanded] = useState(false);
  const s = STATUS_STYLE[log.status] || STATUS_STYLE.skipped;
  const Icon = STATUS_ICON[log.status] || SkipForward;

  const totalDuration = (log.trace || []).reduce((sum, t) => sum + (t.duration_ms || 0), 0);
  const nodeCount = (log.trace || []).length;
  const failCount = (log.trace || []).filter((t) => t.status === "failed").length;

  return (
    <div className="border border-white/[0.06] rounded-xl overflow-hidden bg-white/[0.01]">
      <button onClick={() => setExpanded(!expanded)} className="w-full flex items-center gap-4 px-5 py-4 hover:bg-white/[0.03] transition-colors">
        {expanded ? <ChevronDown className="w-4 h-4 text-white/30 shrink-0" /> : <ChevronRight className="w-4 h-4 text-white/30 shrink-0" />}
        <Icon className={`w-5 h-5 ${s.color} shrink-0`} />
        <div className="flex-1 text-left min-w-0">
          <div className="text-sm text-white/80 font-mono">{log.execution_id.slice(0, 12)}...</div>
          <div className="text-[10px] text-white/30 mt-0.5">{new Date(log.created_at).toLocaleString()}</div>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          <Badge variant="outline" className={`text-[10px] px-2 py-0.5 ${s.bg} ${s.color} ${s.border}`}>
            {log.status}
          </Badge>
          {failCount > 0 && (
            <Badge className="bg-red-500/15 text-red-400 border-red-500/25 text-[10px] px-2 py-0.5">{failCount} failed</Badge>
          )}
          <span className="text-xs text-white/40 font-mono">{nodeCount} nodes</span>
          <span className="text-xs text-white/30 font-mono w-20 text-right">{totalDuration.toFixed(1)}ms</span>
        </div>
      </button>
      {expanded && (
        <div className="px-5 pb-5 space-y-2 border-t border-white/[0.06] pt-4">
          {(log.trace || []).map((entry, idx) => (
            <TraceNodeDetail key={idx} entry={entry} />
          ))}
          {(!log.trace || log.trace.length === 0) && (
            <p className="text-xs text-white/20 text-center py-4">No trace data available.</p>
          )}
        </div>
      )}
    </div>
  );
}

export default function LogsPage({
  params,
}: {
  params: Promise<{ fileId: string }>;
}) {
  const { fileId } = use(params);
  const [logs, setLogs] = useState<ExecutionLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  // True when the last fetch returned fewer rows than requested
  const [reachedEnd, setReachedEnd] = useState(false);
  const { getToken } = useAuth();
  const router = useRouter();

  const fetchLogs = useCallback(async (limit = 50) => {
    try {
      const token = await getToken();
      const res = await axios.get(
        `${API_URL}/api/files/${fileId}/logs?limit=${limit}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setLogs(res.data);
      setReachedEnd(res.data.length < limit);
      setLoadError(null);
    } catch (err) {
      setLoadError(apiErrorMessage(err, "Failed to load execution logs"));
      toast.error("Failed to load execution logs");
    }
  }, [fileId, getToken]);

  useEffect(() => {
    setLoading(true);
    fetchLogs(50).finally(() => setLoading(false));
  }, [fetchLogs]);

  const loadMore = async () => {
    setLoadingMore(true);
    await fetchLogs(logs.length + 50);
    setLoadingMore(false);
  };

  const successCount = logs.filter((l) => l.status === "success").length;
  const failedCount = logs.filter((l) => l.status === "failed").length;

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white">
      <Navbar />
      <div className="max-w-5xl mx-auto p-6">
        {/* header */}
        <div className="flex items-center gap-4 mb-8">
          <Button
            variant="ghost"
            size="icon"
            className="h-9 w-9 text-white/40 hover:text-white hover:bg-white/10"
            onClick={() => router.push(`/files/${fileId}`)}
          >
            <ArrowLeft className="w-4 h-4" />
          </Button>
          <div className="flex-1">
            <h1 className="text-xl font-bold text-white/90 flex items-center gap-2.5">
              <ScrollText className="w-5 h-5 text-indigo-400" />
              Execution Logs
            </h1>
            <p className="text-white/30 text-sm mt-0.5">
              Full execution history for this workflow
            </p>
          </div>
          <div className="flex items-center gap-3">
            {logs.length > 0 && (
              <>
                <Badge variant="outline" className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20 text-xs px-2.5 py-1">
                  {successCount} success
                </Badge>
                {failedCount > 0 && (
                  <Badge variant="outline" className="bg-red-500/10 text-red-400 border-red-500/20 text-xs px-2.5 py-1">
                    {failedCount} failed
                  </Badge>
                )}
              </>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => { setLoading(true); fetchLogs(50).finally(() => setLoading(false)); }}
              disabled={loading}
              className="text-white/40 hover:text-white hover:bg-white/10 gap-1.5"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
              Refresh
            </Button>
          </div>
        </div>

        {/* content */}
        {loading ? (
          <div className="flex flex-col items-center justify-center py-24 gap-4">
            <Loader2 className="w-6 h-6 text-indigo-400 animate-spin" />
            <span className="text-sm text-white/30">Loading execution logs...</span>
          </div>
        ) : loadError && logs.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 gap-4 text-center">
            <XCircle className="w-12 h-12 text-red-400/40" />
            <p className="text-white/50 text-sm">Couldn&apos;t load execution logs.</p>
            <p className="text-white/30 text-xs max-w-sm">{loadError}</p>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => { setLoading(true); fetchLogs(50).finally(() => setLoading(false)); }}
              className="text-indigo-400 hover:text-indigo-300 hover:bg-indigo-500/10 mt-2"
            >
              Try again
            </Button>
          </div>
        ) : logs.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 gap-4 text-center">
            <ScrollText className="w-12 h-12 text-white/10" />
            <p className="text-white/30 text-sm">No executions yet.</p>
            <p className="text-white/20 text-xs max-w-sm">
              Deploy and trigger your workflow to see execution logs and traces here.
            </p>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => router.push(`/files/${fileId}`)}
              className="text-indigo-400 hover:text-indigo-300 hover:bg-indigo-500/10 mt-2"
            >
              Back to Editor
            </Button>
          </div>
        ) : (
          <div className="space-y-3">
            {logs.map((log) => (
              <ExecutionLogRow key={log.id} log={log} />
            ))}
            {!reachedEnd && (
            <div className="flex justify-center pt-4 pb-8">
              <Button
                variant="ghost"
                size="sm"
                onClick={loadMore}
                disabled={loadingMore}
                className="text-white/30 hover:text-white hover:bg-white/10"
              >
                {loadingMore ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                Load More
              </Button>
            </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
