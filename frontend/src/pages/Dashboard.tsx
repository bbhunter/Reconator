import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  Activity,
  CheckCircle2,
  CircleAlert,
  Clock,
  ListChecks,
} from "lucide-react";

import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StatusBadge } from "@/components/StatusBadge";
import { Button } from "@/components/ui/button";
import { formatRelative } from "@/lib/utils";

export function Dashboard() {
  const stats = useQuery({
    queryKey: ["stats"],
    queryFn: api.stats,
    refetchInterval: 5000,
  });
  const recent = useQuery({
    queryKey: ["recent-targets"],
    queryFn: () => api.listTargets({ page: 1, page_size: 6 }),
    refetchInterval: 5000,
  });

  const cards = [
    { label: "Queued", value: stats.data?.queued ?? 0, icon: Clock, color: "text-cyan-400" },
    { label: "Running", value: stats.data?.running ?? 0, icon: Activity, color: "text-amber-400" },
    { label: "Completed", value: stats.data?.completed ?? 0, icon: CheckCircle2, color: "text-emerald-400" },
    { label: "Failed", value: stats.data?.failed ?? 0, icon: CircleAlert, color: "text-rose-400" },
  ];

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
          <p className="text-sm text-muted-foreground">
            Recon queue health and recent activity.
          </p>
        </div>
        <Button asChild>
          <Link to="/targets">
            <ListChecks /> Manage targets
          </Link>
        </Button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {cards.map((c) => (
          <Card key={c.label}>
            <CardHeader className="flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {c.label}
              </CardTitle>
              <c.icon className={`h-4 w-4 ${c.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-semibold">{c.value}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent targets</CardTitle>
        </CardHeader>
        <CardContent>
          {recent.data?.items.length ? (
            <ul className="divide-y divide-border">
              {recent.data.items.map((t) => (
                <li key={t.id} className="py-3 flex items-center justify-between">
                  <Link
                    to={`/targets/${t.id}`}
                    className="font-mono text-sm hover:text-primary"
                  >
                    {t.url}
                  </Link>
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-muted-foreground">
                      {formatRelative(t.created_at)}
                    </span>
                    <StatusBadge status={t.status} />
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">No targets yet.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
