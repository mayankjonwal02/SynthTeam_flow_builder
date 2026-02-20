import { PlayCircle } from "lucide-react"; import { createDBNode } from "./DBNodeFactory";
const a = { border: "border-blue-400", bg: "bg-blue-500/10", text: "text-blue-400", shadow: "shadow-blue-500/5" };
export default createDBNode({ componentName: "pg_txn_start", defaultLabel: "PG Txn Start", accentColor: "blue", accentClasses: a, opBadge: "BEGIN", icon: PlayCircle, fields: ["connection_id"] });
