"use client";

import { UserButton, useUser } from "@clerk/nextjs";
import { Separator } from "@/components/ui/separator";
import { Layers } from "lucide-react";
import Link from "next/link";

export default function Navbar() {
  const { user } = useUser();

  return (
    <div className="w-full border-b border-white/[0.06] bg-[#0d0d14]/90 backdrop-blur-xl sticky top-0 z-50">
      <div className="flex items-center justify-between px-6 py-3 max-w-7xl mx-auto">
        <Link href="/dashboard" className="flex items-center gap-2.5 group">
          <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center">
            <Layers className="w-4 h-4 text-white" />
          </div>
          <span className="text-lg font-bold text-white/90 group-hover:text-white transition-colors">
            SynthTeam
          </span>
        </Link>

        <div className="flex items-center gap-4">
          <div className="text-sm text-white/40">
            {user?.primaryEmailAddress?.emailAddress}
          </div>
          <UserButton
            appearance={{
              elements: {
                avatarBox: "w-8 h-8",
              },
            }}
          />
        </div>
      </div>
    </div>
  );
}
