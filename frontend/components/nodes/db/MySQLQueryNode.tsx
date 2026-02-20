import { TerminalSquare } from "lucide-react"; import { createDBNode } from "./DBNodeFactory";
const a = { border: "border-orange-400", bg: "bg-orange-500/10", text: "text-orange-400", shadow: "shadow-orange-500/5" };
export default createDBNode({ componentName: "mysql_raw_query", defaultLabel: "MySQL Query", accentColor: "orange", accentClasses: a, opBadge: "SQL", icon: TerminalSquare, fields: ["connection_id", "query"] });
