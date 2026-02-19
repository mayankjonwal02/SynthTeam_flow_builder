"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogDescription,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { FilePlus } from "lucide-react";

export default function CreateFlowModal({
  onCreated,
}: {
  onCreated: (name: string) => void;
}) {
  const [name, setName] = useState("");
  const [open, setOpen] = useState(false);

  const create = async () => {
    if (!name.trim()) return;
    const fileName = name.trim().endsWith(".json")
      ? name.trim()
      : `${name.trim()}.json`;
    await onCreated(fileName);
    setName("");
    setOpen(false);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button className="bg-indigo-600 hover:bg-indigo-500 text-white gap-2">
          <FilePlus className="w-4 h-4" />
          New Flow
        </Button>
      </DialogTrigger>

      <DialogContent className="bg-[#13131f] border-white/[0.08] text-white">
        <DialogHeader>
          <DialogTitle className="text-white/90">Create New Flow</DialogTitle>
          <DialogDescription className="text-white/30">
            Give your flow a name. It will be saved as a .json file.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <Input
            placeholder="e.g. my-workflow"
            value={name}
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && create()}
            autoFocus
            className="bg-white/5 border-white/10 text-white placeholder-white/25 focus-visible:ring-indigo-500/50"
          />

          <Button
            onClick={create}
            className="w-full bg-indigo-600 hover:bg-indigo-500 text-white"
          >
            Create Flow
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
