"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Node, Edge } from "reactflow";
import {
  Sparkle, Send, X, Loader2, Bot, User, Settings2,
  ClipboardCheck, Pencil, Wand2, Search, MessageSquareText,
} from "lucide-react";
import axios from "axios";
import { useAgentWebSocket, WSEvent } from "@/hooks/useAgentWebSocket";

interface ChatMsg {
  id: string;
  role: "user" | "assistant";
  content: string;
  agent?: string;
}

const AGENT_BADGE: Record<string, { label: string; cls: string; icon: any }> = {
  requirement: { label: "Requirement", cls: "text-blue-400 bg-blue-500/15 border-blue-500/25", icon: ClipboardCheck },
  planner:     { label: "Planner",     cls: "text-amber-400 bg-amber-500/15 border-amber-500/25", icon: Pencil },
  builder:     { label: "Builder",     cls: "text-emerald-400 bg-emerald-500/15 border-emerald-500/25", icon: Wand2 },
  reviewer:    { label: "Reviewer",    cls: "text-violet-400 bg-violet-500/15 border-violet-500/25", icon: Search },
  feedback:    { label: "Feedback",    cls: "text-orange-400 bg-orange-500/15 border-orange-500/25", icon: MessageSquareText },
};

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Props {
  nodes: Node[];
  edges: Edge[];
  setNodes: (updater: (nodes: Node[]) => Node[]) => void;
  setEdges: (updater: (edges: Edge[]) => Edge[]) => void;
  onClose: () => void;
}

export default function AICopilotPanel({ nodes, edges, setNodes, setEdges, onClose }: Props) {
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [thinking, setThinking] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [showConfig, setShowConfig] = useState(false);
  const [apiKey, setApiKey] = useState("");
  const [provider, setProvider] = useState("ollama");
  const [model, setModel] = useState("llama3.1:8b");
  const [ollamaModels, setOllamaModels] = useState<string[]>([]);
  const [ollamaLoading, setOllamaLoading] = useState(false);
  const [ollamaError, setOllamaError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, thinking]);

  useEffect(() => {
    let cancelled = false;
    if (provider !== "ollama") return;

    setOllamaLoading(true);
    setOllamaError(null);

    axios
      .get(`${API}/agent/ollama/models`)
      .then((res) => {
        if (cancelled) return;
        const models = Array.isArray(res.data?.models) ? res.data.models : [];
        setOllamaModels(models);
        if (models.length) {
          setModel((prev) => (models.includes(prev) ? prev : models[0]));
        }
      })
      .catch((err) => {
        if (cancelled) return;
        setOllamaModels([]);
        setOllamaError(err?.response?.data?.detail || "Failed to load Ollama models");
      })
      .finally(() => {
        if (cancelled) return;
        setOllamaLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [provider]);

  const addMsg = useCallback((msg: ChatMsg) => {
    setMessages((prev) => [...prev, msg]);
  }, []);

  const handleWSEvent = useCallback(
    (event: WSEvent) => {
      const { type, data } = event;
      switch (type) {
        case "agent_thinking":
          setThinking(data.agent || "agent");
          break;
        case "agent_message":
          setThinking(null);
          addMsg({ id: Date.now().toString(), role: "assistant", content: data.content || "", agent: data.agent });
          break;
        case "agent_done":
          setThinking(null);
          break;
        case "node_added":
          setNodes((prev) => [...prev, data as Node]);
          break;
        case "edge_added":
          setEdges((prev) => [...prev, data as Edge]);
          break;
        case "node_updated":
          setNodes((prev) => prev.map((n) => n.id === data.id ? { ...n, data: { ...n.data, config: data.config } } : n));
          break;
        case "node_deleted":
          setNodes((prev) => prev.filter((n) => n.id !== data.id));
          setEdges((prev) => prev.filter((e) => e.source !== data.id && e.target !== data.id));
          break;
        case "status_change":
          if (data.status === "approved" || data.status === "completed") {
            setThinking(null);
            setBusy(false);
          }
          break;
        case "needs_input":
          setThinking(null);
          setBusy(false);
          break;
        case "error":
          setThinking(null);
          setBusy(false);
          addMsg({ id: Date.now().toString(), role: "assistant", content: `Error: ${data.message || JSON.stringify(data)}`, agent: data.agent });
          break;
      }
    },
    [addMsg, setNodes, setEdges]
  );

  const { connected } = useAgentWebSocket({ sessionId, onEvent: handleWSEvent });

  const pollSession = useCallback(async (sid: string) => {
    try {
      const res = await axios.get(`${API}/agent/session/${sid}`);
      const session = res.data;
      if (session.artifacts?.graph) {
        const g = session.artifacts.graph;
        if (g.nodes?.length) setNodes(() => g.nodes);
        if (g.edges?.length) setEdges(() => g.edges);
      }
      if (session.conversation?.length) {
        const msgs: ChatMsg[] = session.conversation
          .filter((m: any) => m.content)
          .map((m: any, i: number) => ({
            id: `sync-${i}`,
            role: m.role,
            content: m.content,
            agent: m.agent,
          }));
        if (msgs.length > messages.length) setMessages(msgs);
      }
      if (session.status === "approved" || session.status === "completed") {
        setBusy(false);
      }
    } catch {}
  }, [setNodes, setEdges, messages.length]);

  useEffect(() => {
    if (!sessionId || !connected) return;
    const t = setTimeout(() => pollSession(sessionId), 1500);
    const t2 = setTimeout(() => pollSession(sessionId), 5000);
    return () => { clearTimeout(t); clearTimeout(t2); };
  }, [sessionId, connected, pollSession]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || busy) return;
    setInput("");

    addMsg({ id: Date.now().toString(), role: "user", content: text });
    setBusy(true);

    try {
      if (!sessionId) {
        const body: any = {
          prompt: text,
          llm_provider: provider,
          llm_model: model,
        };
        if (apiKey.trim()) body.api_key = apiKey.trim();
        const res = await axios.post(`${API}/agent/session/start`, body);
        setSessionId(res.data.session_id);
      } else {
        await axios.post(`${API}/agent/session/${sessionId}/message`, { message: text });
      }
    } catch (err: any) {
      setBusy(false);
      addMsg({
        id: Date.now().toString(),
        role: "assistant",
        content: `Failed: ${err?.response?.data?.detail || err.message}`,
      });
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#0d0d14]">
      {/* Header */}
      <div className="shrink-0 flex items-center justify-between px-3 py-2.5 border-b border-white/[0.06]">
        <div className="flex items-center gap-2">
          <Sparkle className="w-4 h-4 text-purple-400" />
          <span className="text-xs font-semibold text-white/70">AI Copilot</span>
          {sessionId && (
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          )}
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setShowConfig((p) => !p)}
            className="p-1 text-white/30 hover:text-white/60 transition-colors rounded"
          >
            <Settings2 className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={onClose}
            className="p-1 text-white/30 hover:text-white/60 transition-colors rounded"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Config panel */}
      {showConfig && (
        <div className="shrink-0 border-b border-white/[0.06] p-3 space-y-2 bg-white/[0.02]">
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="text-[9px] uppercase tracking-widest text-white/30 font-semibold">Provider</label>
              <select
                value={provider}
                onChange={(e) => setProvider(e.target.value)}
                className="w-full bg-white/[0.06] border border-white/10 rounded px-2 py-1 text-[11px] text-white focus:outline-none mt-0.5"
              >
                {["ollama", "openai", "anthropic", "gemini", "groq", "mistral"].map((p) => (
                  <option key={p} value={p} className="bg-[#0d0d14]">{p}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-[9px] uppercase tracking-widest text-white/30 font-semibold">Model</label>
              {provider === "ollama" && ollamaModels.length > 0 ? (
                <select
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  disabled={ollamaLoading}
                  className="w-full bg-white/[0.06] border border-white/10 rounded px-2 py-1 text-[11px] text-white font-mono focus:outline-none mt-0.5 disabled:opacity-60"
                >
                  {ollamaModels.map((m) => (
                    <option key={m} value={m} className="bg-[#0d0d14]">
                      {m}
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  placeholder={provider === "ollama" ? "llama3.1:8b" : "gpt-4o-mini"}
                  className="w-full bg-white/[0.06] border border-white/10 rounded px-2 py-1 text-[11px] text-white font-mono focus:outline-none mt-0.5"
                />
              )}
              {provider === "ollama" && (
                <div className="mt-1 text-[10px] text-white/35">
                  {ollamaLoading
                    ? "Loading Ollama models…"
                    : ollamaError
                    ? `Ollama: ${ollamaError}`
                    : ollamaModels.length === 0
                    ? "No models returned from Ollama. You can still type a model name."
                    : null}
                </div>
              )}
            </div>
          </div>
          <div>
            <label className="text-[9px] uppercase tracking-widest text-white/30 font-semibold">API Key</label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="sk-..."
              className="w-full bg-white/[0.06] border border-white/10 rounded px-2 py-1 text-[11px] text-white font-mono placeholder-white/20 focus:outline-none mt-0.5"
            />
          </div>
        </div>
      )}

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-3 py-3 space-y-2.5">
        {messages.length === 0 && !thinking && (
          <div className="text-center py-10 space-y-3">
            <Sparkle className="w-8 h-8 text-purple-400/30 mx-auto" />
            <div className="text-sm text-white/30">Describe what you want to build</div>
            <div className="text-[11px] text-white/15 max-w-[250px] mx-auto leading-relaxed">
              e.g. "Add an LLM call node that takes user input and returns a response"
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id} className={`flex gap-2 ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            {msg.role === "assistant" && (
              <div className="shrink-0 w-6 h-6 rounded-full bg-white/10 flex items-center justify-center mt-0.5">
                {msg.agent && AGENT_BADGE[msg.agent] ? (
                  (() => { const Icon = AGENT_BADGE[msg.agent!].icon; return <Icon className="w-3 h-3 text-white/50" />; })()
                ) : (
                  <Bot className="w-3 h-3 text-white/50" />
                )}
              </div>
            )}
            <div className={`max-w-[85%] rounded-lg px-2.5 py-1.5 text-[12px] leading-relaxed ${
              msg.role === "user"
                ? "bg-purple-600/25 text-white border border-purple-500/15"
                : "bg-white/[0.05] text-white/75 border border-white/[0.05]"
            }`}>
              {msg.agent && msg.role === "assistant" && AGENT_BADGE[msg.agent] && (
                <span className={`inline-block text-[8px] font-bold uppercase tracking-wider px-1 py-0.5 rounded border mb-1 ${AGENT_BADGE[msg.agent].cls}`}>
                  {AGENT_BADGE[msg.agent].label}
                </span>
              )}
              <div className="whitespace-pre-wrap break-words">{msg.content}</div>
            </div>
            {msg.role === "user" && (
              <div className="shrink-0 w-6 h-6 rounded-full bg-purple-600/25 flex items-center justify-center mt-0.5">
                <User className="w-3 h-3 text-purple-400" />
              </div>
            )}
          </div>
        ))}

        {thinking && (
          <div className="flex gap-2 items-center">
            <div className="w-6 h-6 rounded-full bg-white/10 flex items-center justify-center">
              <Loader2 className="w-3 h-3 text-white/40 animate-spin" />
            </div>
            <span className="text-[11px] text-white/30 italic">
              {AGENT_BADGE[thinking]?.label || "Agent"} is thinking...
            </span>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="shrink-0 border-t border-white/[0.06] p-2.5">
        <div className="flex gap-1.5">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
            disabled={busy}
            placeholder={busy ? "Agents working..." : sessionId ? "Ask a follow-up..." : "Describe what to build..."}
            className="flex-1 bg-white/[0.05] border border-white/10 rounded-lg px-2.5 py-1.5 text-[12px] text-white placeholder-white/25 focus:outline-none focus:border-purple-500/30 disabled:opacity-40"
          />
          <button
            onClick={handleSend}
            disabled={busy || !input.trim()}
            className="bg-purple-600 hover:bg-purple-500 disabled:opacity-25 text-white rounded-lg px-2.5 transition-colors"
          >
            <Send className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}
