"use client";

import { useState } from "react";
import { useAuth } from "@clerk/nextjs";
import axios from "axios";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { FileCode2, Copy, Check, Loader2, Download } from "lucide-react";

interface OpenApiModalProps {
  projectId: string;
}

export default function OpenApiModal({ projectId }: OpenApiModalProps) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [json, setJson] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const { getToken } = useAuth();

  const fetchOpenApi = async () => {
    setLoading(true);
    setJson(null);
    try {
      const token = await getToken();
      const res = await axios.get(
        `http://localhost:8000/api/projects/${projectId}/openapi`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setJson(JSON.stringify(res.data, null, 2));
    } catch (err: any) {
      const msg = err?.response?.data?.detail || "Failed to fetch OpenAPI spec";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleOpen = (isOpen: boolean) => {
    setOpen(isOpen);
    if (isOpen) {
      fetchOpenApi();
    } else {
      // reset on close
      setCopied(false);
    }
  };

  const handleCopy = async () => {
    if (!json) return;
    await navigator.clipboard.writeText(json);
    setCopied(true);
    toast.success("Copied to clipboard");
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    if (!json) return;
    const blob = new Blob([json], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `openapi-${projectId}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success("Downloaded openapi.json");
  };

  const hasEndpoints = json ? JSON.parse(json).paths && Object.keys(JSON.parse(json).paths).length > 0 : false;

  return (
    <Dialog open={open} onOpenChange={handleOpen}>
      <Tooltip>
        <TooltipTrigger asChild>
          <DialogTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="h-9 w-9 text-white/40 hover:text-indigo-400 hover:bg-indigo-500/10 border border-transparent hover:border-indigo-500/20 transition-all"
            >
              <FileCode2 className="w-4.5 h-4.5" />
            </Button>
          </DialogTrigger>
        </TooltipTrigger>
        <TooltipContent>View OpenAPI JSON</TooltipContent>
      </Tooltip>

      <DialogContent className="max-w-3xl bg-[#0d0d14] border-white/[0.08] text-white p-0 gap-0 overflow-hidden">
        <DialogHeader className="px-6 pt-6 pb-4 border-b border-white/[0.06]">
          <DialogTitle className="text-lg font-semibold flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-500/15 border border-indigo-500/25 flex items-center justify-center">
              <FileCode2 className="w-4 h-4 text-indigo-400" />
            </div>
            OpenAPI Specification
          </DialogTitle>
          <DialogDescription className="text-white/35 text-sm mt-1">
            Auto-generated from active deployed flows in this project.
          </DialogDescription>
        </DialogHeader>

        <div className="relative">
          {/* action buttons */}
          {json && !loading && (
            <div className="absolute top-3 right-3 z-10 flex items-center gap-2">
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 bg-white/5 hover:bg-white/10 text-white/50 hover:text-white border border-white/[0.06] rounded-lg"
                    onClick={handleDownload}
                  >
                    <Download className="w-3.5 h-3.5" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Download JSON</TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className={`h-8 w-8 border rounded-lg transition-all ${
                      copied
                        ? "bg-emerald-500/15 border-emerald-500/30 text-emerald-400"
                        : "bg-white/5 hover:bg-white/10 text-white/50 hover:text-white border-white/[0.06]"
                    }`}
                    onClick={handleCopy}
                  >
                    {copied ? (
                      <Check className="w-3.5 h-3.5" />
                    ) : (
                      <Copy className="w-3.5 h-3.5" />
                    )}
                  </Button>
                </TooltipTrigger>
                <TooltipContent>{copied ? "Copied!" : "Copy to clipboard"}</TooltipContent>
              </Tooltip>
            </div>
          )}

          {/* content */}
          <div className="max-h-[60vh] overflow-auto">
            {loading ? (
              <div className="flex flex-col items-center justify-center py-20 gap-3">
                <Loader2 className="w-6 h-6 text-indigo-400 animate-spin" />
                <span className="text-sm text-white/30">Generating OpenAPI spec…</span>
              </div>
            ) : json ? (
              !hasEndpoints ? (
                <div className="flex flex-col items-center justify-center py-20 gap-3 text-center px-6">
                  <FileCode2 className="w-10 h-10 text-white/10" />
                  <p className="text-white/30 text-sm">No active endpoints found.</p>
                  <p className="text-white/20 text-xs max-w-sm">
                    Deploy one or more flows in this project to generate an OpenAPI specification.
                  </p>
                </div>
              ) : (
                <pre className="p-6 text-xs leading-relaxed font-mono text-white/70 whitespace-pre overflow-x-auto">
                  <code>{json}</code>
                </pre>
              )
            ) : (
              <div className="flex flex-col items-center justify-center py-20 gap-3">
                <FileCode2 className="w-10 h-10 text-white/10" />
                <span className="text-sm text-white/30">Failed to load spec</span>
              </div>
            )}
          </div>
        </div>

        {/* footer */}
        {json && hasEndpoints && !loading && (
          <div className="px-6 py-3 border-t border-white/[0.06] flex items-center justify-between">
            <span className="text-xs text-white/20">
              {Object.keys(JSON.parse(json).paths).length} endpoint{Object.keys(JSON.parse(json).paths).length !== 1 ? "s" : ""}
            </span>
            <Button
              onClick={handleCopy}
              size="sm"
              className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs px-4 gap-1.5 rounded-lg"
            >
              {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
              {copied ? "Copied" : "Copy JSON"}
            </Button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
