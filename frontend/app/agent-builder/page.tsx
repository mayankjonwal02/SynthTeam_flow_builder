"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Wand2, Loader2, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { apiErrorMessage, useApi } from "@/lib/api";

const EXAMPLES = [
  "Build a REST API with authentication that logs every request to PostgreSQL",
  "Create a chatbot API that uses GPT-4 with web search and memory",
  "Build a RAG pipeline: ingest documents via API, then query them for answers",
  "Create a multi-step data pipeline: fetch from external API, process, and store in MongoDB",
];

export default function AgentBuilderStart() {
  const router = useRouter();
  const api = useApi();
  const [prompt, setPrompt] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [loading, setLoading] = useState(false);
  const [provider, setProvider] = useState("ollama");
  const [model, setModel] = useState("llama3.1:8b");

  const [ollamaModels, setOllamaModels] = useState<string[]>([]);
  const [ollamaLoading, setOllamaLoading] = useState(false);
  const [ollamaError, setOllamaError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    if (provider !== "ollama") return;

    setOllamaLoading(true);
    setOllamaError(null);

    api
      .get("/agent/ollama/models")
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
  }, [provider, api]);

  const handleStart = async () => {
    if (!prompt.trim()) return;
    setLoading(true);
    try {
      const body: Record<string, string> = {
        prompt: prompt.trim(),
        llm_provider: provider,
        llm_model: model,
      };
      if (apiKey.trim()) body.api_key = apiKey.trim();
      const res = await api.post("/agent/session/start", body);
      const sessionId = res.data.session_id;
      router.push(`/agent-builder/${sessionId}`);
    } catch (err) {
      toast.error(apiErrorMessage(err, "Failed to start session"));
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a12] flex items-center justify-center p-6">
      <div className="w-full max-w-2xl space-y-8">
        {/* Header */}
        <div className="text-center space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-purple-500/10 border border-purple-500/20">
            <Sparkles className="w-4 h-4 text-purple-400" />
            <span className="text-xs font-semibold text-purple-400 uppercase tracking-wider">AI Workflow Builder</span>
          </div>
          <h1 className="text-3xl font-bold text-white">Describe your workflow</h1>
          <p className="text-sm text-white/40 max-w-md mx-auto">
            Tell us what you want to build. Our AI agents will design, build, and review
            the workflow for you.
          </p>
        </div>

        {/* Prompt input */}
        <div className="space-y-3">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            rows={4}
            placeholder="I want to build a..."
            className="w-full bg-white/[0.04] border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-white/25 focus:outline-none focus:border-purple-500/40 resize-none"
          />

          {/* Examples */}
          <div className="flex flex-wrap gap-2">
            {EXAMPLES.map((ex, i) => (
              <button
                key={i}
                onClick={() => setPrompt(ex)}
                className="text-[11px] text-white/40 hover:text-white/70 bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.06] rounded-lg px-2.5 py-1.5 transition-colors text-left"
              >
                {ex}
              </button>
            ))}
          </div>
        </div>

        {/* Config */}
        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="text-[10px] uppercase tracking-widest text-white/30 font-semibold mb-1 block">Provider</label>
            <select
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              className="w-full bg-white/[0.04] border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none"
            >
              {["ollama", "openai", "anthropic", "gemini", "groq", "mistral"].map((p) => (
                <option key={p} value={p} className="bg-[#0a0a12]">{p}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-[10px] uppercase tracking-widest text-white/30 font-semibold mb-1 block">Model</label>
            {provider === "ollama" && ollamaModels.length > 0 ? (
              <select
                value={model}
                onChange={(e) => setModel(e.target.value)}
                disabled={ollamaLoading}
                className="w-full bg-white/[0.04] border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none font-mono disabled:opacity-60"
              >
                {ollamaModels.map((m) => (
                  <option key={m} value={m} className="bg-[#0a0a12]">
                    {m}
                  </option>
                ))}
              </select>
            ) : (
              <input
                value={model}
                onChange={(e) => setModel(e.target.value)}
                placeholder={provider === "ollama" ? "llama3.1:8b" : "gpt-4o-mini"}
                className="w-full bg-white/[0.04] border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-white/25 focus:outline-none font-mono"
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
          <div>
            <label className="text-[10px] uppercase tracking-widest text-white/30 font-semibold mb-1 block">API Key (optional)</label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="sk-..."
              className="w-full bg-white/[0.04] border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-white/25 focus:outline-none font-mono"
            />
          </div>
        </div>

        {/* Start button */}
        <button
          onClick={handleStart}
          disabled={loading || !prompt.trim()}
          className="w-full flex items-center justify-center gap-2 bg-purple-600 hover:bg-purple-500 disabled:opacity-40 disabled:hover:bg-purple-600 text-white font-semibold py-3 rounded-xl transition-colors"
        >
          {loading ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Wand2 className="w-5 h-5" />
          )}
          {loading ? "Starting agents..." : "Build with AI Agents"}
        </button>
      </div>
    </div>
  );
}
