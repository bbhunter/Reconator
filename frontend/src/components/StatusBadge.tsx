import { Badge } from "@/components/ui/badge";
import type { ModuleStatus, TargetStatus } from "@/lib/api";

const map: Record<TargetStatus | ModuleStatus, { variant: any; label: string }> = {
  queued: { variant: "info", label: "Queued" },
  pending: { variant: "outline", label: "Pending" },
  running: { variant: "warning", label: "Running" },
  completed: { variant: "success", label: "Completed" },
  failed: { variant: "destructive", label: "Failed" },
  cancelled: { variant: "secondary", label: "Cancelled" },
  skipped: { variant: "secondary", label: "Skipped" },
};

export function StatusBadge({ status }: { status: TargetStatus | ModuleStatus }) {
  const m = map[status] ?? { variant: "outline", label: status };
  return <Badge variant={m.variant}>{m.label}</Badge>;
}
