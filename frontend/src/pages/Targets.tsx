import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Plus, Search, Trash2 } from "lucide-react";

import { api, type TargetStatus } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { StatusBadge } from "@/components/StatusBadge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { useToast } from "@/hooks/use-toast";
import { formatRelative } from "@/lib/utils";

const tabs: { id: "all" | TargetStatus; label: string }[] = [
  { id: "all", label: "All" },
  { id: "queued", label: "Queued" },
  { id: "running", label: "Running" },
  { id: "completed", label: "Completed" },
  { id: "failed", label: "Failed" },
];

export function Targets() {
  const qc = useQueryClient();
  const { toast } = useToast();
  const [tab, setTab] = useState<"all" | TargetStatus>("all");
  const [search, setSearch] = useState("");
  const [open, setOpen] = useState(false);
  const [url, setUrl] = useState("");

  const targets = useQuery({
    queryKey: ["targets", tab, search],
    queryFn: () =>
      api.listTargets({
        status: tab === "all" ? undefined : tab,
        search: search || undefined,
        page_size: 100,
      }),
    refetchInterval: 5000,
  });

  const create = useMutation({
    mutationFn: (u: string) => api.createTarget(u),
    onSuccess: (t) => {
      toast({ title: "Queued", description: t.url });
      setOpen(false);
      setUrl("");
      qc.invalidateQueries({ queryKey: ["targets"] });
      qc.invalidateQueries({ queryKey: ["stats"] });
    },
    onError: (e: Error) =>
      toast({ variant: "destructive", title: "Failed", description: e.message }),
  });

  const remove = useMutation({
    mutationFn: (id: number) => api.deleteTarget(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["targets"] });
      qc.invalidateQueries({ queryKey: ["stats"] });
    },
    onError: (e: Error) =>
      toast({ variant: "destructive", title: "Failed", description: e.message }),
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Targets</h1>
          <p className="text-sm text-muted-foreground">
            Add a domain to queue a recon scan.
          </p>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus /> Add target
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add a target</DialogTitle>
              <DialogDescription>
                Enter a bare domain (e.g. example.com). The worker picks it up automatically.
              </DialogDescription>
            </DialogHeader>
            <Input
              placeholder="example.com"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && url.trim()) create.mutate(url.trim());
              }}
            />
            <DialogFooter>
              <Button
                disabled={!url.trim() || create.isPending}
                onClick={() => create.mutate(url.trim())}
              >
                Queue scan
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between gap-4 space-y-0">
          <Tabs value={tab} onValueChange={(v) => setTab(v as any)}>
            <TabsList>
              {tabs.map((t) => (
                <TabsTrigger key={t.id} value={t.id}>
                  {t.label}
                </TabsTrigger>
              ))}
            </TabsList>
          </Tabs>
          <div className="relative w-full max-w-xs">
            <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              className="pl-8"
              placeholder="Search domains"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </CardHeader>
        <CardContent>
          {targets.isLoading ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : !targets.data?.items.length ? (
            <p className="text-sm text-muted-foreground">No targets match.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Domain</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Queued</TableHead>
                  <TableHead>Completed</TableHead>
                  <TableHead className="w-12"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {targets.data.items.map((t) => (
                  <TableRow key={t.id}>
                    <TableCell>
                      <Link
                        to={`/targets/${t.id}`}
                        className="font-mono text-sm hover:text-primary"
                      >
                        {t.url}
                      </Link>
                      {t.error && (
                        <p className="text-xs text-rose-400 mt-0.5">{t.error}</p>
                      )}
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={t.status} />
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {formatRelative(t.created_at)}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {formatRelative(t.completed_at)}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        size="icon"
                        variant="ghost"
                        title="Delete"
                        onClick={() => remove.mutate(t.id)}
                      >
                        <Trash2 className="text-rose-400" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
