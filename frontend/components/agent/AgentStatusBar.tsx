"use client";

import { ClipboardCheck, Pencil, Wand2, Search, MessageSquareText, Loader2, CheckCircle2, Circle } from "lucide-react";

export type AgentStatus = "idle" | "thinking" | "done" | "error";

interface Props {
  statuses: Record<string, AgentStatus>;
}

const AGENTS = [
  { key: "requirement", label: "Requirement", icon: ClipboardCheck,    color: "blue" },
  { key: "planner",     label: "Planner",     icon: Pencil,            color: "amber" },
  { key: "builder",     label: "Builder",     icon: Wand2,             color: "emerald" },
  { key: "reviewer",    label: "Reviewer",    icon: Search,            color: "violet" },
  { key: "feedback",    label: "Feedback",    icon: MessageSquareText, color: "orange" },
];

const STATUS_INDICATOR: Record<AgentStatus, { icon: any; className: string }> = {
  idle:     { icon: Circle,       className: "text-white/20" },
  thinking: { icon: Loader2,      className: "text-yellow-400 animate-spin" },
  done:     { icon: CheckCircle2, className: "text-emerald-400" },
  error:    { icon: Circle,       className: "text-red-400" },
};

export default function AgentStatusBar({ statuses }: Props) {
  return (
    <div className="flex items-center gap-6 px-5 py-2.5 bg-[#0d0d14] border-t border-white/[0.06]">
      <span className="text-[9px] uppercase tracking-[0.2em] text-white/30 font-semibold">Agents</span>

      {AGENTS.map(({ key, label, icon: AgentIcon, color }) => {
        const status = statuses[key] || "idle";
        const { icon: StatusIcon, className: statusClass } = STATUS_INDICATOR[status];

        return (
          <div key={key} className="flex items-center gap-1.5">
            <AgentIcon className={`w-3.5 h-3.5 text-${color}-400/60`} />
            <span className="text-[11px] text-white/50 font-medium">{label}</span>
            <StatusIcon className={`w-3 h-3 ${statusClass}`} />
          </div>
        );
      })}
    </div>
  );
}
