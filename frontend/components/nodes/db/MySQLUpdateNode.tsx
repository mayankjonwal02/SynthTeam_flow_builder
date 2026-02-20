import { PenLine } from "lucide-react"; import { createDBNode } from "./DBNodeFactory";
const a = { border: "border-orange-400", bg: "bg-orange-500/10", text: "text-orange-400", shadow: "shadow-orange-500/5" };
export default createDBNode({ componentName: "mysql_update", defaultLabel: "MySQL Update", accentColor: "orange", accentClasses: a, opBadge: "UPDATE", icon: PenLine, fields: ["connection_id", "table", "filters"] });
