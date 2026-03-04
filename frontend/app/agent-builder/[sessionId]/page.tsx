"use client";

import { use, useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";
import { ArrowLeft, Save, CheckCircle2, Loader2, KeyRound, X } from "lucide-react";
import { Node, Edge } from "reactflow";

import AgentChatPanel, { ChatMessage } from "@/components/agent/AgentChatPanel";
import AgentCanvas from "@/components/agent/AgentCanvas";
import AgentStatusBar, { AgentStatus } from "@/components/agent/AgentStatusBar";
import { useAgentWebSocket, WSEvent } from "@/hooks/useAgentWebSocket";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function AgentBuilderSession({
  params,
}: {
  params: Promise<{ sessionId: string }>;
}) {
  const { sessionId } = use(params);
  const router = useRouter();

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [status, setStatus] = useState("active");
  const [thinking, setThinking] = useState<string | null>(null);
  const [agentStatuses, setAgentStatuses] = useState<Record<string, AgentStatus>>({
    requirement: "idle",
    planner: "idle",
    builder: "idle",
    reviewer: "idle",
    feedback: "idle",
  });
  const [saving, setSaving] = useState(false);
  const [inputDisabled, setInputDisabled] = useState(true);
  const [secretsModal, setSecretsModal] = useState<{
    open: boolean;
    fields: { node_id: string; node_label: string; field_key: string; field_label: string }[];
  }>({ open: false, fields: [] });
  const [secretValues, setSecretValues] = useState<Record<string, Record<string, string>>>({});
  const [submittingSecrets, setSubmittingSecrets] = useState(false);

  const addMessage = useCallback((msg: ChatMessage) => {
    setMessages((prev) => [...prev, msg]);
  }, []);

  const handleWSEvent = useCallback(
    (event: WSEvent) => {
      const { type, data } = event;

      switch (type) {
        case "agent_thinking":
          setThinking(data.agent || null);
          setInputDisabled(true);
          if (data.agent) {
            setAgentStatuses((prev) => ({ ...prev, [data.agent]: "thinking" }));
          }
          break;

        case "agent_message":
          setThinking(null);
          addMessage({
            id: Date.now().toString(),
            role: "assistant",
            content: data.content || JSON.stringify(data),
            agent: data.agent,
          });
          break;

        case "agent_done":
          setThinking(null);
          if (data.agent) {
            setAgentStatuses((prev) => ({
              ...prev,
              [data.agent]: data.success === false ? "error" : "done",
            }));
          }
          break;

        case "node_added":
          setNodes((prev) => [...prev, data as Node]);
          break;

        case "edge_added":
          setEdges((prev) => [...prev, data as Edge]);
          break;

        case "node_updated":
          setNodes((prev) =>
            prev.map((n) =>
              n.id === data.id ? { ...n, data: { ...n.data, config: data.config } } : n
            )
          );
          break;

        case "node_deleted":
          setNodes((prev) => prev.filter((n) => n.id !== data.id));
          setEdges((prev) =>
            prev.filter((e) => e.source !== data.id && e.target !== data.id)
          );
          break;

        case "status_change":
          setStatus(data.status || "active");
          if (data.status === "approved" || data.status === "completed") {
            setInputDisabled(false);
            setThinking(null);
          }
          break;

        case "needs_input":
          setInputDisabled(false);
          setThinking(null);
          if (data.reason === "secrets_needed" && data.fields?.length) {
            const init: Record<string, Record<string, string>> = {};
            for (const f of data.fields) {
              if (!init[f.node_id]) init[f.node_id] = {};
              init[f.node_id][f.field_key] = "";
            }
            setSecretValues(init);
            setSecretsModal({ open: true, fields: data.fields });
          }
          break;

        case "error":
          setThinking(null);
          setInputDisabled(false);
          addMessage({
            id: Date.now().toString(),
            role: "assistant",
            content: `Error: ${data.message || JSON.stringify(data)}`,
            agent: data.agent,
          });
          break;

        default:
          break;
      }
    },
    [addMessage]
  );

  const { connected } = useAgentWebSocket({
    sessionId,
    onEvent: handleWSEvent,
  });

  const syncSession = useCallback(() => {
    axios
      .get(`${API}/agent/session/${sessionId}`)
      .then((res) => {
        const session = res.data;
        setStatus(session.status || "active");

        if (session.conversation?.length) {
          const msgs: ChatMessage[] = session.conversation
            .filter((m: any) => m.content)
            .map((m: any, i: number) => ({
              id: `hist-${i}`,
              role: m.role,
              content: m.content,
              agent: m.agent,
            }));
          setMessages((prev) => (msgs.length > prev.length ? msgs : prev));
        }

        if (session.artifacts?.graph) {
          const g = session.artifacts.graph;
          setNodes((prev) => (g.nodes?.length && g.nodes.length !== prev.length ? g.nodes : prev));
          setEdges((prev) => (g.edges?.length && g.edges.length !== prev.length ? g.edges : prev));
        }

        if (session.status === "approved" || session.status === "completed") {
          setInputDisabled(false);
          setThinking(null);
        }
      })
      .catch(() => {});
  }, [sessionId]);

  useEffect(() => {
    syncSession();
  }, [syncSession]);

  useEffect(() => {
    if (!connected) return;
    const t1 = setTimeout(syncSession, 2000);
    const t2 = setTimeout(syncSession, 6000);
    return () => { clearTimeout(t1); clearTimeout(t2); };
  }, [connected, syncSession]);

  const handleSend = useCallback(
    async (text: string) => {
      addMessage({
        id: Date.now().toString(),
        role: "user",
        content: text,
      });
      setInputDisabled(true);

      try {
        await axios.post(`${API}/agent/session/${sessionId}/message`, {
          message: text,
        });
      } catch {
        setInputDisabled(false);
      }
    },
    [sessionId, addMessage]
  );

  const handleSave = useCallback(async () => {
    setSaving(true);
    try {
      const res = await axios.post(
        `${API}/agent/session/${sessionId}/save?project_id=`
      );
      alert(`Saved! File ID: ${res.data.file_id}`);
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Save failed");
    }
    setSaving(false);
  }, [sessionId]);

  const handleApprove = useCallback(async () => {
    await axios.post(`${API}/agent/session/${sessionId}/approve`);
    setStatus("completed");
  }, [sessionId]);

  const handleSubmitSecrets = useCallback(async () => {
    setSubmittingSecrets(true);
    try {
      await axios.post(`${API}/agent/session/${sessionId}/secrets`, {
        secrets: secretValues,
      });
      setSecretsModal({ open: false, fields: [] });
      setInputDisabled(true);
      addMessage({
        id: Date.now().toString(),
        role: "user",
        content: "Secrets provided. Resuming workflow review...",
      });
      await axios.post(`${API}/agent/session/${sessionId}/message`, {
        message: "Secrets have been submitted. Please continue with the review.",
      });
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Failed to submit secrets");
    }
    setSubmittingSecrets(false);
  }, [sessionId, secretValues, addMessage]);

  const statusLabel =
    status === "approved"
      ? "Approved"
      : status === "completed"
      ? "Completed"
      : status === "failed"
      ? "Failed"
      : "In Progress";

  const statusColor =
    status === "approved" || status === "completed"
      ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
      : status === "failed"
      ? "bg-red-500/20 text-red-400 border-red-500/30"
      : "bg-blue-500/20 text-blue-400 border-blue-500/30";

  return (
    <div className="h-screen flex flex-col bg-[#0a0a12]">
      {/* Header */}
      <div className="shrink-0 flex items-center justify-between px-4 py-2.5 border-b border-white/[0.06] bg-[#0d0d14]">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.push("/agent-builder")}
            className="text-white/40 hover:text-white/70 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <h1 className="text-sm font-semibold text-white/80">AI Workflow Builder</h1>
          <span
            className={`text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${statusColor}`}
          >
            {statusLabel}
          </span>
          {connected && (
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" title="WebSocket connected" />
          )}
        </div>

        <div className="flex items-center gap-2">
          {status === "approved" && (
            <button
              onClick={handleApprove}
              className="flex items-center gap-1.5 text-xs font-medium text-emerald-400 bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/20 rounded-lg px-3 py-1.5 transition-colors"
            >
              <CheckCircle2 className="w-3.5 h-3.5" />
              Approve
            </button>
          )}
          <button
            onClick={handleSave}
            disabled={saving || nodes.length === 0}
            className="flex items-center gap-1.5 text-xs font-medium text-white/70 bg-white/[0.06] hover:bg-white/10 border border-white/10 rounded-lg px-3 py-1.5 transition-colors disabled:opacity-30"
          >
            {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
            Save Workflow
          </button>
        </div>
      </div>

      {/* Main split pane */}
      <div className="flex-1 flex min-h-0">
        {/* Canvas */}
        <div className="flex-1 relative">
          <AgentCanvas nodes={nodes} edges={edges} />
        </div>

        {/* Chat panel */}
        <div className="w-[380px] border-l border-white/[0.06]">
          <AgentChatPanel
            messages={messages}
            onSend={handleSend}
            disabled={inputDisabled}
            thinking={thinking}
          />
        </div>
      </div>

      {/* Status bar */}
      <AgentStatusBar statuses={agentStatuses} />

      {/* Secrets Modal */}
      {secretsModal.open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-[#12121e] border border-white/10 rounded-2xl shadow-2xl w-full max-w-lg mx-4">
            <div className="flex items-center justify-between px-6 py-4 border-b border-white/[0.06]">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-amber-500/15 border border-amber-500/30 flex items-center justify-center">
                  <KeyRound className="w-4 h-4 text-amber-400" />
                </div>
                <div>
                  <h2 className="text-sm font-semibold text-white">Secrets Required</h2>
                  <p className="text-[11px] text-white/40">
                    {secretsModal.fields.length} field(s) need your input
                  </p>
                </div>
              </div>
              <button
                onClick={() => setSecretsModal({ open: false, fields: [] })}
                className="text-white/30 hover:text-white/60 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="px-6 py-4 space-y-3 max-h-[60vh] overflow-y-auto">
              {secretsModal.fields.map((field, i) => (
                <div key={`${field.node_id}-${field.field_key}`} className="space-y-1.5">
                  <div className="flex items-baseline gap-2">
                    <span className="text-[11px] font-semibold text-white/70">{field.field_label}</span>
                    <span className="text-[10px] text-white/30 font-mono">
                      {field.node_label}
                    </span>
                  </div>
                  <input
                    type="password"
                    value={secretValues[field.node_id]?.[field.field_key] || ""}
                    onChange={(e) =>
                      setSecretValues((prev) => ({
                        ...prev,
                        [field.node_id]: {
                          ...prev[field.node_id],
                          [field.field_key]: e.target.value,
                        },
                      }))
                    }
                    placeholder={`Enter ${field.field_label.toLowerCase()}...`}
                    className="w-full bg-white/[0.04] border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-white/20 focus:outline-none focus:border-amber-500/40 font-mono"
                  />
                </div>
              ))}
            </div>

            <div className="px-6 py-4 border-t border-white/[0.06] flex justify-end gap-2">
              <button
                onClick={() => setSecretsModal({ open: false, fields: [] })}
                className="px-4 py-2 text-xs text-white/50 hover:text-white/70 transition-colors"
              >
                Skip
              </button>
              <button
                onClick={handleSubmitSecrets}
                disabled={submittingSecrets}
                className="flex items-center gap-2 px-4 py-2 text-xs font-semibold bg-amber-600 hover:bg-amber-500 disabled:opacity-40 text-white rounded-lg transition-colors"
              >
                {submittingSecrets ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <KeyRound className="w-3.5 h-3.5" />
                )}
                Submit Secrets
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
