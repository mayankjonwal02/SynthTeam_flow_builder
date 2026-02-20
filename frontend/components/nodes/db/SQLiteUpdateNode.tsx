import { PenLine } from "lucide-react"; import { createDBNode } from "./DBNodeFactory";
const a = { border: "border-amber-400", bg: "bg-amber-500/10", text: "text-amber-400", shadow: "shadow-amber-500/5" };
export default createDBNode({ componentName: "sqlite_update", defaultLabel: "SQLite Update", accentColor: "amber", accentClasses: a, opBadge: "UPDATE", icon: PenLine, fields: ["connection_id", "table", "filters"] });
