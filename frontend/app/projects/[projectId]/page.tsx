"use client";

import { use, useEffect, useState } from "react";
import axios from "axios";
import Link from "next/link";
import { useAuth } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import Navbar from "@/components/Navbar";
import CreateFlowModal from "@/components/CreateFlowModal";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { toast } from "sonner";
import {
  ArrowLeft,
  FileJson,
  ArrowRight,
  Circle,
  Power,
  Loader2,
} from "lucide-react";
import OpenApiModal from "@/components/OpenApiModal";

export default function ProjectPage({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = use(params);
  const [files, setFiles] = useState<any[]>([]);
  const [toggling, setToggling] = useState<string | null>(null); // file id being toggled
  const { getToken } = useAuth();
  const router = useRouter();

  const load = async () => {
    try {
      const token = await getToken();
      const res = await axios.get(
        `http://localhost:8000/api/files/project/${projectId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setFiles(res.data);
    } catch {
      toast.error("Failed to load files");
    }
  };

  const createFile = async (name: string) => {
    try {
      const token = await getToken();
      await axios.post(
        "http://localhost:8000/api/files",
        { project_id: projectId, name },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success("Flow created");
      load();
    } catch {
      toast.error("Failed to create flow");
    }
  };

  const toggleDeploy = async (fileId: string, isCurrentlyLive: boolean) => {
    setToggling(fileId);
    try {
      const token = await getToken();
      if (isCurrentlyLive) {
        await axios.post(
          `http://localhost:8000/api/files/undeploy/${fileId}`,
          {},
          { headers: { Authorization: `Bearer ${token}` } }
        );
        toast.success("Flow stopped");
      } else {
        const res = await axios.post(
          `http://localhost:8000/api/files/deploy/${fileId}`,
          {},
          { headers: { Authorization: `Bearer ${token}` } }
        );
        toast.success(
          `Deployed: ${res.data.method} ${res.data.endpoint}`
        );
      }
      load();
    } catch (err: any) {
      const msg =
        err?.response?.data?.detail || err?.message || "Toggle failed";
      toast.error(isCurrentlyLive ? "Failed to stop" : "Failed to deploy", {
        description: msg,
      });
    } finally {
      setToggling(null);
    }
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white">
      <Navbar />
      <div className="p-6 max-w-7xl mx-auto">
        {/* ── header ── */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-white/40 hover:text-white hover:bg-white/10"
              onClick={() => router.push("/dashboard")}
            >
              <ArrowLeft className="w-4 h-4" />
            </Button>
            <div>
              <h1 className="text-2xl font-bold text-white/90">
                Project Flows
              </h1>
              <p className="text-white/30 text-sm mt-0.5">
                Create and manage visual API workflows
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <OpenApiModal projectId={projectId} />
            <CreateFlowModal onCreated={createFile} />
          </div>
        </div>

        {/* ── files grid ── */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {files.map((f) => {
            const isLive = f.is_deployed;
            const isTogglingThis = toggling === f.id;

            return (
              <Card
                key={f.id}
                className="bg-[#0d0d14] border-white/[0.06] hover:border-white/[0.15] hover:bg-white/[0.02] transition-all duration-200 group shadow-none relative"
              >
                <CardContent className="p-5">
                  <div className="flex items-start justify-between">
                    <Link href={`/files/${f.id}`} className="flex items-center gap-3 flex-1 min-w-0">
                      <div
                        className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 border ${
                          isLive
                            ? "bg-emerald-500/10 border-emerald-500/20"
                            : "bg-blue-500/10 border-blue-500/20"
                        }`}
                      >
                        <FileJson className={`w-4 h-4 ${isLive ? "text-emerald-400" : "text-blue-400"}`} />
                      </div>
                      <div className="min-w-0">
                        <div className="font-semibold text-white/80 group-hover:text-white transition-colors truncate">
                          {f.name}
                        </div>
                        <div className="flex items-center gap-2 mt-1">
                          {isLive ? (
                            <Badge className="bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 text-[9px] gap-1 px-1.5 py-0">
                              <Circle className="w-1.5 h-1.5 fill-emerald-400 animate-pulse" />
                              Live
                            </Badge>
                          ) : (
                            <Badge variant="outline" className="bg-white/5 text-white/30 border-white/10 text-[9px] gap-1 px-1.5 py-0">
                              <Circle className="w-1.5 h-1.5 fill-white/20" />
                              Stopped
                            </Badge>
                          )}
                          {f.deployed_path && isLive && (
                            <span className="text-[9px] text-white/20 font-mono truncate">
                              {f.deployed_method} {f.deployed_path}
                            </span>
                          )}
                        </div>
                      </div>
                    </Link>

                    <div className="flex items-center gap-1.5 shrink-0 ml-2">
                      {/* ── toggle live/stop button ── */}
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <button
                            onClick={(e) => {
                              e.preventDefault();
                              e.stopPropagation();
                              toggleDeploy(f.id, isLive);
                            }}
                            disabled={isTogglingThis}
                            className={`w-7 h-7 rounded-lg flex items-center justify-center border transition-all ${
                              isTogglingThis
                                ? "border-white/10 text-white/20"
                                : isLive
                                ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20"
                                : "border-white/10 bg-white/5 text-white/30 hover:bg-white/10 hover:text-white/50"
                            }`}
                          >
                            {isTogglingThis ? (
                              <Loader2 className="w-3.5 h-3.5 animate-spin" />
                            ) : (
                              <Power className="w-3.5 h-3.5" />
                            )}
                          </button>
                        </TooltipTrigger>
                        <TooltipContent>
                          {isLive ? "Stop this flow" : "Deploy this flow"}
                        </TooltipContent>
                      </Tooltip>

                      <Link href={`/files/${f.id}`}>
                        <ArrowRight className="w-4 h-4 text-white/10 group-hover:text-white/30 transition-colors" />
                      </Link>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}

          {files.length === 0 && (
            <div className="col-span-full text-center text-white/20 mt-16">
              <FileJson className="w-12 h-12 mx-auto mb-3 text-white/10" />
              <p className="text-sm">No flows yet. Create your first flow.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
