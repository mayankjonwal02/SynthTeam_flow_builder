import { PenLine } from "lucide-react"; import { createDBNode } from "./DBNodeFactory";
const a = { border: "border-blue-400", bg: "bg-blue-500/10", text: "text-blue-400", shadow: "shadow-blue-500/5" };
export default createDBNode({ componentName: "pg_update", defaultLabel: "PG Update", accentColor: "blue", accentClasses: a, opBadge: "UPDATE", icon: PenLine, fields: ["connection_id", "table", "filters"] });
