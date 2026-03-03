"use client";

import { useRef, useEffect, useState } from "react";
import { Bot, User, Send, Loader2, ClipboardCheck, Pencil, Search, Wand2, MessageSquareText } from "lucide-react";

const AGENT_META: Record<string, { label: string; color: string; icon: any }> = {
  requirement: { label: "Requirement", color: "text-blue-400 bg-blue-500/20 border-blue-500/30", icon: ClipboardCheck },
  planner:     { label: "Planner",     color: "text-amber-400 bg-amber-500/20 border-amber-500/30", icon: Pencil },
  builder:     { label: "Builder",     color: "text-emerald-400 bg-emerald-500/20 border-emerald-500/30", icon: Wand2 },
  reviewer:    { label: "Reviewer",    color: "text-violet-400 bg-violet-500/20 border-violet-500/30", icon: Search },
  feedback:    { label: "Feedback",    color: "text-orange-400 bg-orange-500/20 border-orange-500/30", icon: MessageSquareText },
};

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  agent?: string;
  timestamp?: string;
}

interface Props {
  messages: ChatMessage[];
  onSend: (text: string) => void;
  disabled?: boolean;
  thinking?: string | null;
}

export default function AgentChatPanel({ messages, onSend, disabled, thinking }: Props) {
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, thinking]);

  const handleSend = () => {
    const text = input.trim();
    if (!text || disabled) return;
    onSend(text);
    setInput("");
  };

  return (
    <div className="flex flex-col h-full bg-[#0d0d14]">
      {/* Header */}
      <div className="shrink-0 px-4 py-3 border-b border-white/[0.06]">
        <h3 className="text-sm font-semibold text-white/70">Agent Chat</h3>
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
        {messages.map((msg) => (
          <div key={msg.id} className={`flex gap-2 ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            {msg.role === "assistant" && (
              <div className="shrink-0 w-7 h-7 rounded-full bg-white/10 flex items-center justify-center mt-0.5">
                {msg.agent && AGENT_META[msg.agent] ? (
                  (() => { const Icon = AGENT_META[msg.agent!].icon; return <Icon className="w-3.5 h-3.5 text-white/60" />; })()
                ) : (
                  <Bot className="w-3.5 h-3.5 text-white/60" />
                )}
              </div>
            )}

            <div className={`max-w-[80%] rounded-xl px-3 py-2 text-[13px] leading-relaxed ${
              msg.role === "user"
                ? "bg-blue-600/30 text-white border border-blue-500/20"
                : "bg-white/[0.06] text-white/80 border border-white/[0.06]"
            }`}>
              {msg.agent && msg.role === "assistant" && AGENT_META[msg.agent] && (
                <span className={`inline-block text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded border mb-1.5 ${AGENT_META[msg.agent].color}`}>
                  {AGENT_META[msg.agent].label}
                </span>
              )}
              <div className="whitespace-pre-wrap break-words">{msg.content}</div>
            </div>

            {msg.role === "user" && (
              <div className="shrink-0 w-7 h-7 rounded-full bg-blue-600/30 flex items-center justify-center mt-0.5">
                <User className="w-3.5 h-3.5 text-blue-400" />
              </div>
            )}
          </div>
        ))}

        {thinking && (
          <div className="flex gap-2 items-center">
            <div className="shrink-0 w-7 h-7 rounded-full bg-white/10 flex items-center justify-center">
              <Loader2 className="w-3.5 h-3.5 text-white/50 animate-spin" />
            </div>
            <span className="text-xs text-white/40 italic">
              {AGENT_META[thinking]?.label || "Agent"} is thinking...
            </span>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="shrink-0 border-t border-white/[0.06] p-3">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
            disabled={disabled}
            placeholder={disabled ? "Agents are working..." : "Type a message..."}
            className="flex-1 bg-white/[0.06] border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-white/30 focus:outline-none focus:border-white/20 disabled:opacity-40"
          />
          <button
            onClick={handleSend}
            disabled={disabled || !input.trim()}
            className="bg-blue-600 hover:bg-blue-500 disabled:opacity-30 disabled:hover:bg-blue-600 text-white rounded-lg px-3 transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
