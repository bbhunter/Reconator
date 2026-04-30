import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Download } from "lucide-react";

import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StatusBadge } from "@/components/StatusBadge";
import { formatRelative } from "@/lib/utils";

export function TargetDetail() {
  const { id } = useParams<{ id: string }>();
  const targetId = Number(id);
  const [active, setActive] = useState<string | null>(null);

  const detail = useQuery({
    queryKey: ["target", targetId],
    queryFn: () => api.getTarget(targetId),
    refetchInterval: (q) => {
      const s = q.state.data?.status;
      return s === "queued" || s === "running" ? 5000 : false;
    },
  });

  const result = useQuery({
    queryKey: ["result", targetId, active],
    queryFn: () => api.getResult(targetId, active!),
    enabled: !!active,
  });

  if (detail.isLoading) {
    return <p className="text-sm text-muted-foreground">Loading…</p>;
  }
  if (!detail.data) {
    return <p className="text-sm text-rose-400">Target not found.</p>;
  }

  const t = detail.data;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Button asChild size="icon" variant="ghost">
            <Link to="/targets">
              <ArrowLeft />
            </Link>
          </Button>
          <div>
            <h1 className="text-2xl font-semibold font-mono">{t.url}</h1>
            <p className="text-xs text-muted-foreground">
              Queued {formatRelative(t.created_at)} · Started {formatRelative(t.started_at)} · Completed {formatRelative(t.completed_at)}
            </p>
          </div>
        </div>
        <StatusBadge status={t.status} />
      </div>

      {t.error && (
        <Card>
          <CardContent className="py-3 text-sm text-rose-400">{t.error}</CardContent>
        </Card>
      )}

      <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Modules</CardTitle>
          </CardHeader>
          <CardContent className="px-2">
            {t.results.length === 0 ? (
              <p className="text-sm text-muted-foreground px-2">
                Nothing to show yet — modules run as the worker progresses.
              </p>
            ) : (
              <ul className="space-y-0.5">
                {t.results.map((r) => (
                  <li key={r.module}>
                    <button
                      onClick={() => setActive(r.module)}
                      className={`w-full flex items-center justify-between px-3 py-2 rounded-md text-left text-sm transition-colors ${
                        active === r.module
                          ? "bg-secondary text-foreground"
                          : "hover:bg-secondary/60 text-muted-foreground"
                      }`}
                    >
                      <span className="font-mono">{r.module}</span>
                      <StatusBadge status={r.status} />
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card className="overflow-hidden">
          <CardHeader className="flex-row items-center justify-between">
            <CardTitle className="font-mono text-base">
              {active ?? "Select a module"}
            </CardTitle>
            {active && result.data?.has_output && (
              <Button asChild size="sm" variant="outline">
                <a
                  href={api.downloadResult(targetId, active)}
                  target="_blank"
                  rel="noreferrer"
                >
                  <Download /> Download
                </a>
              </Button>
            )}
          </CardHeader>
          <CardContent>
            {!active ? (
              <p className="text-sm text-muted-foreground">
                Pick a module from the list to view its output.
              </p>
            ) : result.isLoading ? (
              <p className="text-sm text-muted-foreground">Loading…</p>
            ) : result.data?.error && !result.data?.output ? (
              <p className="text-sm text-rose-400">{result.data.error}</p>
            ) : (
              <pre className="text-xs leading-relaxed bg-secondary/40 rounded-md p-4 overflow-auto max-h-[60vh] whitespace-pre-wrap break-words">
                {result.data?.output || "(empty)"}
              </pre>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
