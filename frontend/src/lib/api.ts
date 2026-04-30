const BASE = import.meta.env.VITE_API_URL || "";
const PREFIX = "/api/v1";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${PREFIX}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {}
    throw new Error(detail);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export type TargetStatus =
  | "queued"
  | "running"
  | "completed"
  | "failed"
  | "cancelled";

export type ModuleStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "skipped";

export interface Target {
  id: number;
  url: string;
  status: TargetStatus;
  error: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface ScanResultSummary {
  module: string;
  status: ModuleStatus;
  completed_at: string | null;
  has_output: boolean;
}

export interface ScanResult extends ScanResultSummary {
  id: number;
  output: string | null;
  error: string | null;
  started_at: string | null;
}

export interface TargetDetail extends Target {
  results: ScanResultSummary[];
}

export interface TargetList {
  items: Target[];
  total: number;
  page: number;
  page_size: number;
}

export interface Stats {
  queued: number;
  running: number;
  completed: number;
  failed: number;
  total: number;
}

export interface ModuleInfo {
  name: string;
  description: string;
  timeout: number;
}

export const api = {
  listTargets: (params: {
    status?: TargetStatus;
    search?: string;
    page?: number;
    page_size?: number;
  } = {}) => {
    const qs = new URLSearchParams();
    if (params.status) qs.set("status", params.status);
    if (params.search) qs.set("search", params.search);
    qs.set("page", String(params.page ?? 1));
    qs.set("page_size", String(params.page_size ?? 25));
    return request<TargetList>(`/targets?${qs.toString()}`);
  },
  getTarget: (id: number) => request<TargetDetail>(`/targets/${id}`),
  createTarget: (url: string) =>
    request<Target>("/targets", {
      method: "POST",
      body: JSON.stringify({ url }),
    }),
  deleteTarget: (id: number) =>
    request<void>(`/targets/${id}`, { method: "DELETE" }),
  stats: () => request<Stats>("/targets/stats"),
  listResults: (targetId: number) =>
    request<ScanResult[]>(`/targets/${targetId}/results`),
  getResult: (targetId: number, module: string) =>
    request<ScanResult>(`/targets/${targetId}/results/${module}`),
  downloadResult: (targetId: number, module: string) =>
    `${BASE}${PREFIX}/targets/${targetId}/results/${module}/download`,
  modules: () => request<ModuleInfo[]>("/modules"),
};
