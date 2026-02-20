"use client";

import { Link2, Type, Code2 } from "lucide-react";

export type FieldMode = "static" | "input" | "expression";

interface FieldModeInputProps {
  mode: FieldMode;
  value: string;
  onModeChange: (mode: FieldMode) => void;
  onValueChange: (value: string) => void;
  placeholder?: {
    static?: string;
    input?: string;
    expression?: string;
  };
  accentColor?: string;
}

const MODE_STYLES: Record<FieldMode, { bg: string; text: string; border: string }> = {
  static: { bg: "bg-violet-500/15", text: "text-violet-400", border: "border-violet-500/25" },
  input: { bg: "bg-cyan-500/15", text: "text-cyan-400", border: "border-cyan-500/25" },
  expression: { bg: "bg-amber-500/15", text: "text-amber-400", border: "border-amber-500/25" },
};

const MODE_ICONS: Record<FieldMode, React.ReactNode> = {
  static: <Type className="w-3 h-3" />,
  input: <Link2 className="w-3 h-3" />,
  expression: <Code2 className="w-3 h-3" />,
};

const MODE_LABELS: Record<FieldMode, string> = {
  static: "Static",
  input: "Input",
  expression: "Expr",
};

const MODE_ORDER: FieldMode[] = ["static", "input", "expression"];

export default function FieldModeInput({
  mode,
  value,
  onModeChange,
  onValueChange,
  placeholder = {},
}: FieldModeInputProps) {
  const cycleMode = () => {
    const currentIdx = MODE_ORDER.indexOf(mode);
    const nextIdx = (currentIdx + 1) % MODE_ORDER.length;
    onModeChange(MODE_ORDER[nextIdx]);
  };

  const styles = MODE_STYLES[mode];

  const defaultPlaceholders: Record<FieldMode, string> = {
    static: "fixed value",
    input: "fieldName",
    expression: "input.data.nested.field",
  };

  const hints: Record<FieldMode, string> = {
    static: "Literal value, used as-is",
    input: "Flat key from upstream data",
    expression: "Dot-path into nested data",
  };

  const placeholderText = placeholder[mode] || defaultPlaceholders[mode];

  return (
    <div className="space-y-1">
      <div className="flex items-center gap-1.5">
        <button
          onClick={cycleMode}
          className={`flex items-center gap-1 text-[10px] font-semibold px-2 py-1 rounded-md border transition-all shrink-0 ${styles.bg} ${styles.text} ${styles.border}`}
          title={`Click to cycle: Static → Input → Expression`}
        >
          {MODE_ICONS[mode]}
          {MODE_LABELS[mode]}
        </button>
        <input
          value={value}
          onChange={(e) => onValueChange(e.target.value)}
          placeholder={placeholderText}
          className="flex-1 bg-white/5 border border-white/10 rounded-md px-2 py-1 text-xs text-white placeholder-white/20 focus:outline-none focus:border-white/30 font-mono"
        />
      </div>
      <div className={`text-[9px] pl-[58px] ${styles.text} opacity-60`}>{hints[mode]}</div>
    </div>
  );
}
