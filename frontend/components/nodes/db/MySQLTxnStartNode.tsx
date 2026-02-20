import { PlayCircle } from "lucide-react"; import { createDBNode } from "./DBNodeFactory";
const a = { border: "border-orange-400", bg: "bg-orange-500/10", text: "text-orange-400", shadow: "shadow-orange-500/5" };
export default createDBNode({ componentName: "mysql_txn_start", defaultLabel: "MySQL Txn Start", accentColor: "orange", accentClasses: a, opBadge: "BEGIN", icon: PlayCircle, fields: ["connection_id"] });
