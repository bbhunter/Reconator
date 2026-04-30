import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function Modules() {
  const modules = useQuery({ queryKey: ["modules"], queryFn: api.modules });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Modules</h1>
        <p className="text-sm text-muted-foreground">
          Recon checks the worker runs against every target.
        </p>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {modules.data?.map((m) => (
          <Card key={m.name}>
            <CardHeader className="pb-2">
              <CardTitle className="font-mono text-sm">{m.name}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">{m.description}</p>
              <p className="text-xs text-muted-foreground mt-2">
                Timeout: {m.timeout}s
              </p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
