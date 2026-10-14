"use client";

import { useEffect, useState } from "react";
import axios from "axios";
import { API_URL } from "@/lib/api";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import CreateProjectModal from "@/components/CreateProjectModal";
import { Card, CardContent } from "@/components/ui/card";
import { useAuth } from "@clerk/nextjs";
import { toast } from "sonner";
import { FolderOpen, FileJson, Workflow, ArrowRight } from "lucide-react";

export default function Dashboard() {
  const [projects, setProjects] = useState<any[]>([]);
  const { getToken } = useAuth();

  const load = async () => {
    try {
      const token = await getToken();
      const res = await axios.get(`${API_URL}/api/projects`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setProjects(res.data);
    } catch {
      toast.error("Failed to load projects");
    }
  };

  const createProject = async (name: string) => {
    try {
      const token = await getToken();
      await axios.post(
        `${API_URL}/api/projects`,
        { name },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success("Project created");
      load();
    } catch {
      toast.error("Failed to create project");
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
          <div>
            <h1 className="text-2xl font-bold text-white/90">Dashboard</h1>
            <p className="text-white/30 text-sm mt-1">
              Manage your projects and visual API workflows
            </p>
          </div>
          <CreateProjectModal onCreated={createProject} />
        </div>

        {/* ── stats ── */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <Card className="bg-[#0d0d14] border-white/[0.06] shadow-none">
            <CardContent className="p-5 flex items-center gap-4">
              <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
                <FolderOpen className="w-5 h-5 text-indigo-400" />
              </div>
              <div>
                <div className="text-xs text-white/30 uppercase tracking-wider">
                  Projects
                </div>
                <div className="text-2xl font-bold text-white/80">
                  {projects.length}
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-[#0d0d14] border-white/[0.06] shadow-none">
            <CardContent className="p-5 flex items-center gap-4">
              <div className="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center">
                <FileJson className="w-5 h-5 text-blue-400" />
              </div>
              <div>
                <div className="text-xs text-white/30 uppercase tracking-wider">
                  Flows
                </div>
                <div className="text-2xl font-bold text-white/80">—</div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-[#0d0d14] border-white/[0.06] shadow-none">
            <CardContent className="p-5 flex items-center gap-4">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
                <Workflow className="w-5 h-5 text-emerald-400" />
              </div>
              <div>
                <div className="text-xs text-white/30 uppercase tracking-wider">
                  Deployed
                </div>
                <div className="text-2xl font-bold text-white/80">—</div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* ── section title ── */}
        <div className="mb-4">
          <h2 className="text-sm font-semibold text-white/50 uppercase tracking-wider">
            Your Projects
          </h2>
        </div>

        {/* ── projects grid ── */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {projects.map((p) => (
            <Link key={p.id} href={`/projects/${p.id}`}>
              <Card className="bg-[#0d0d14] border-white/[0.06] cursor-pointer hover:border-white/[0.15] hover:bg-white/[0.02] transition-all duration-200 group shadow-none">
                <CardContent className="p-5">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center shrink-0">
                        <FolderOpen className="w-4 h-4 text-indigo-400" />
                      </div>
                      <div>
                        <div className="font-semibold text-white/80 group-hover:text-white transition-colors">
                          {p.name}
                        </div>
                        <div className="text-[11px] text-white/25 font-mono mt-0.5">
                          {p.id.slice(0, 8)}…
                        </div>
                      </div>
                    </div>
                    <ArrowRight className="w-4 h-4 text-white/10 group-hover:text-white/30 transition-colors mt-1" />
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}

          {projects.length === 0 && (
            <div className="col-span-full text-center text-white/20 mt-16">
              <FolderOpen className="w-12 h-12 mx-auto mb-3 text-white/10" />
              <p className="text-sm">No projects yet. Create your first project.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
