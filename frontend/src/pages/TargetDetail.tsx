import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, Ban, Download, RefreshCcw, Search } from "lucide-react";

import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { StatusBadge } from "@/components/StatusBadge";
import { useToast } from "@/hooks/use-toast";
import { formatRelative } from "@/lib/utils";

function highlight(text: string, query: string) {
  if (!query) return text;
  const lower = text.toLowerCase();
  const q = query.toLowerCase();
  const out: (string | JSX.Element)[] = [];
  let i = 0;
  while (i < text.length) {
    const idx = lower.indexOf(q, i);
    if (idx < 0) {
      out.push(text.slice(i));
      break;
    }
    if (idx > i) out.push(text.slice(i, idx));
    out.push(
      <mark
        key={idx}
        className="bg-amber-400/30 text-foreground rounded-sm"
      >
        {text.slice(idx, idx + q.length)}
      </mark>,
    );
    i = idx + q.length;
  }
  return <>{out}</>;
}

export function TargetDetail() {
  const { id } = useParams<{ id: string }>();
  const targetId = Number(id);
  const qc = useQueryClient();
  const { toast } = useToast();
  const nav = useNavigate();
  const [active, setActive] = useState<string | null>(null);
  const [filter, setFilter] = useState("");

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

  const cancel = useMutation({
    mutationFn: () => api.cancelTarget(targetId),
    onSuccess: () => {
      toast({ title: "Cancellation requested" });
      qc.invalidateQueries({ queryKey: ["target", targetId] });
    },
    onError: (e: Error) =>
      toast({ variant: "destructive", title: "Failed", description: e.message }),
  });

  const rescan = useMutation({
    mutationFn: () => api.rescanTarget(targetId),
    onSuccess: (t) => {
      toast({ title: "Rescan queued", description: `New target #${t.id}` });
      nav(`/targets/${t.id}`);
    },
    onError: (e: Error) =>
      toast({ variant: "destructive", title: "Failed", description: e.message }),
  });

  const filteredOutput = useMemo(() => {
    const out = result.data?.output ?? "";
    if (!filter) return out;
    return out
      .split(/\r?\n/)
      .filter((line) => line.toLowerCase().includes(filter.toLowerCase()))
      .join("\n");
  }, [result.data, filter]);

  if (detail.isLoading) {
    return <p className="text-sm text-muted-foreground">Loading…</p>;
  }
  if (!detail.data) {
    return <p className="text-sm text-rose-400">Target not found.</p>;
  }

  const t = detail.data;
  const canCancel = t.status === "queued" || t.status === "running";

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-3">
          <Button asChild size="icon" variant="ghost">
            <Link to="/targets">
              <ArrowLeft />
            </Link>
          </Button>
          <div>
            <h1 className="text-2xl font-semibold font-mono">{t.url}</h1>
            <p className="text-xs text-muted-foreground">
              Queued {formatRelative(t.created_at)} · Started{" "}
              {formatRelative(t.started_at)} · Completed{" "}
              {formatRelative(t.completed_at)}
            </p>
            {(t.tags || []).length > 0 && (
              <div className="flex gap-1 mt-1">
                {t.tags.map((tg) => (
                  <Badge key={tg} variant="outline">
                    {tg}
                  </Badge>
                ))}
              </div>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <StatusBadge status={t.status} />
          {canCancel && (
            <Button
              size="sm"
              variant="outline"
              onClick={() => cancel.mutate()}
              disabled={cancel.isPending}
            >
              <Ban /> Cancel
            </Button>
          )}
          <Button
            size="sm"
            variant="outline"
            onClick={() => rescan.mutate()}
            disabled={rescan.isPending}
          >
            <RefreshCcw /> Rescan
          </Button>
        </div>
      </div>

      {t.error && (
        <Card>
          <CardContent className="py-3 text-sm text-rose-400">
            {t.error}
          </CardContent>
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
                Nothing yet — modules run as the worker progresses.
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
          <CardHeader className="flex-row items-center justify-between gap-3 flex-wrap">
            <CardTitle className="font-mono text-base">
              {active ?? "Select a module"}
            </CardTitle>
            <div className="flex items-center gap-2">
              {active && (
                <div className="relative w-52">
                  <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    className="pl-8 h-9"
                    placeholder="Filter output"
                    value={filter}
                    onChange={(e) => setFilter(e.target.value)}
                  />
                </div>
              )}
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
            </div>
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
                {highlight(filteredOutput || "(empty)", filter)}
              </pre>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
