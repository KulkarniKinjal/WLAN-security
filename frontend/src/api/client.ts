const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
const API_TOKEN = import.meta.env.VITE_API_TOKEN as string | undefined;

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      ...(API_TOKEN ? { Authorization: `Bearer ${API_TOKEN}` } : {}),
      ...(options.body && !(options.body instanceof FormData) ? { "Content-Type": "application/json" } : {}),
      ...options.headers,
    },
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  if (res.headers.get("content-type")?.includes("application/json")) {
    return res.json();
  }
  return res as unknown as T;
}

export const api = {
  health: () => request<{ status: string; app: string; execution_mode: string }>("/api/health"),
  dashboard: () => request<DashboardData>("/api/dashboard"),
  doctor: () => request<DoctorReport>("/api/doctor"),
  scenarios: () => request<Scenario[]>("/api/registry/scenarios"),
  wordlists: () => request<WordlistItem[]>("/api/uploads/wordlists"),
  uploadCapture: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<UploadResult>("/api/uploads/capture", { method: "POST", body: form });
  },
  createWirelessSession: (payload: { name: string; scenario_id: string; capture_upload_id: string; wordlist_id?: string }) =>
    request<SessionDetail>("/api/sessions/wireless", { method: "POST", body: JSON.stringify(payload) }),
  createMetasploitSession: (payload: { name: string; scenario_id: string }) =>
    request<SessionDetail>("/api/sessions/metasploit", { method: "POST", body: JSON.stringify(payload) }),
  awarenessScenarios: () => request<AwarenessScenario[]>("/api/sessions/awareness/scenarios"),
  dummyCredentials: () => request<{ username: string; password: string }>("/api/sessions/awareness/dummy-credentials"),
  createAwarenessSession: (payload: { name: string; scenario_id: string }) =>
    request<SessionDetail>("/api/sessions/awareness", { method: "POST", body: JSON.stringify(payload) }),
  submitAwareness: (sessionId: string, decisions: Record<string, string>) =>
    request<SessionDetail>(`/api/sessions/awareness/${sessionId}/submit`, { method: "POST", body: JSON.stringify(decisions) }),
  listSessions: (params?: { module?: string; status?: string }) => {
    const qs = new URLSearchParams(params as Record<string, string>).toString();
    return request<SessionListItem[]>(`/api/sessions${qs ? `?${qs}` : ""}`);
  },
  getSession: (id: string) => request<SessionDetail>(`/api/sessions/${id}`),
  cancelSession: (id: string) => request<SessionDetail>(`/api/sessions/${id}/cancel`, { method: "POST" }),
  deleteSession: (id: string) => request<{ deleted: boolean }>(`/api/sessions/${id}`, { method: "DELETE" }),
  pdfReportUrl: (id: string) => `${BASE_URL}/api/reports/${id}.pdf`,
  jsonReportUrl: (id: string) => `${BASE_URL}/api/reports/${id}.json`,
  downloadReport: async (id: string, format: "pdf" | "json") => {
    const response = await fetch(`${BASE_URL}/api/reports/${id}.${format}`, {
      headers: API_TOKEN ? { Authorization: `Bearer ${API_TOKEN}` } : {},
    });
    if (!response.ok) throw new Error(`Report download failed (${response.status})`);
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `attacklab-${id}.${format}`;
    link.click();
    URL.revokeObjectURL(url);
  },
};

export interface DoctorCheck {
  id: string;
  label: string;
  status: "passed" | "warning" | "failed";
  detail: string;
}
export interface DoctorReport {
  overall: "passed" | "warning" | "failed";
  checks: DoctorCheck[];
}

export interface DashboardData {
  environment_readiness: "passed" | "warning" | "failed";
  execution_mode: string;
  status_counts: Record<string, number>;
  recent_sessions: Array<{ id: string; name: string; module: string; status: string; outcome: string; execution_mode: string; created_at: string }>;
  findings_by_module: Record<string, Array<{ id: string; title: string; severity: string; summary: string; created_at: string }>>;
}

export interface Scenario {
  id: string;
  module: string;
  title: string;
  objective: string;
  description: string;
  requires_wordlist: boolean;
  defense: string;
}

export interface WordlistItem {
  id: string;
  name: string;
  size_bytes: number;
}

export interface UploadResult {
  upload_id: string;
  filename: string;
  size_bytes: number;
  metadata: { available: boolean; reason?: string; raw?: string };
}

export interface SessionListItem {
  id: string;
  name: string;
  module: string;
  scenario_id: string;
  status: string;
  outcome: string;
  execution_mode: string;
  created_at: string;
  duration_seconds: number | null;
}

export interface SessionDetail extends SessionListItem {
  fixture_provenance: string;
  input_summary: Record<string, unknown>;
  evidence: Record<string, unknown>;
  explanation: { objective?: string; proves?: string; does_not_prove?: string; defense?: string };
  raw_log: string;
  error_message: string;
  started_at: string | null;
  finished_at: string | null;
}

export interface AwarenessScenario {
  id: string;
  title: string;
  brand: string;
  narrative: string;
  steps: Array<{ id: string; prompt: string; options: string[] }>;
}
