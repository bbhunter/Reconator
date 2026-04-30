const BASE = import.meta.env.VITE_API_URL || "";
const PREFIX = "/api/v1";

const API_KEY_STORAGE = "reconator.apiKey";

export const apiKeyStore = {
  get(): string | null {
    try {
      return localStorage.getItem(API_KEY_STORAGE);
    } catch {
      return null;
    }
  },
  set(value: string) {
    try {
      if (value) localStorage.setItem(API_KEY_STORAGE, value);
      else localStorage.removeItem(API_KEY_STORAGE);
    } catch {}
  },
  clear() {
    try {
      localStorage.removeItem(API_KEY_STORAGE);
    } catch {}
  },
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((init?.headers as Record<string, string>) ?? {}),
  };
  const key = apiKeyStore.get();
  if (key) headers["X-API-Key"] = key;

  const res = await fetch(`${BASE}${PREFIX}${path}`, { ...init, headers });
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
  tags: string[];
  selected_modules: string[] | null;
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
  notes: string | null;
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
  cancelled: number;
  total: number;
  avg_duration_seconds: number | null;
}

export interface ModuleInfo {
  name: string;
  description: string;
  timeout: number;
}

export interface BulkResult {
  created: number[];
  conflicts: string[];
  errors: Record<string, string>;
}

export interface SystemInfo {
  name: string;
  version: string;
  env: string;
  auth_required: boolean;
  notifications: { telegram: boolean; webhook: boolean };
}

export const api = {
  listTargets: (
    params: {
      status?: TargetStatus;
      search?: string;
      tag?: string;
      page?: number;
      page_size?: number;
    } = {},
  ) => {
    const qs = new URLSearchParams();
    if (params.status) qs.set("status", params.status);
    if (params.search) qs.set("search", params.search);
    if (params.tag) qs.set("tag", params.tag);
    qs.set("page", String(params.page ?? 1));
    qs.set("page_size", String(params.page_size ?? 25));
    return request<TargetList>(`/targets?${qs.toString()}`);
  },
  getTarget: (id: number) => request<TargetDetail>(`/targets/${id}`),
  createTarget: (payload: {
    url: string;
    tags?: string[];
    selected_modules?: string[] | null;
    notes?: string | null;
  }) =>
    request<Target>("/targets", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  bulkCreate: (payload: {
    urls: string[];
    tags?: string[];
    selected_modules?: string[] | null;
  }) =>
    request<BulkResult>("/targets/bulk", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  deleteTarget: (id: number) =>
    request<void>(`/targets/${id}`, { method: "DELETE" }),
  cancelTarget: (id: number) =>
    request<Target>(`/targets/${id}/cancel`, { method: "POST" }),
  rescanTarget: (id: number) =>
    request<Target>(`/targets/${id}/rescan`, { method: "POST" }),
  stats: () => request<Stats>("/targets/stats"),
  listResults: (targetId: number) =>
    request<ScanResult[]>(`/targets/${targetId}/results`),
  getResult: (targetId: number, module: string) =>
    request<ScanResult>(`/targets/${targetId}/results/${module}`),
  downloadResult: (targetId: number, module: string) =>
    `${BASE}${PREFIX}/targets/${targetId}/results/${module}/download`,
  exportTargets: (format: "csv" | "json", status?: TargetStatus) => {
    const qs = new URLSearchParams({ format });
    if (status) qs.set("status", status);
    return `${BASE}${PREFIX}/targets/export?${qs.toString()}`;
  },
  modules: () => request<ModuleInfo[]>("/modules"),
  systemInfo: () => request<SystemInfo>("/system/info"),
  testNotify: () =>
    request<{ sent: boolean; enabled: boolean }>("/system/test-notify", {
      method: "POST",
    }),
};
