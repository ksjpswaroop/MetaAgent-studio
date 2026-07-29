import { logger } from "./logger";
import { storageGet, storageSet } from "./storage";

export type SessionDraft = {
  id: string;
  projectId: string;
  projectName: string;
  idea: string;
  stage: string;
};

export type PlanPath = {
  id: string;
  kind: string;
  title: string;
  summary: string;
  asciiFlow: string;
};

export type RoleRow = {
  name: string;
  tierLabel: string;
  blurb: string;
};

export type CheckResult = {
  overall: number;
  packageOk: boolean;
  testsOk: boolean;
  zipOk: boolean;
  summary?: string;
};

export type EdgeItem = { id: string; title: string; detail: string };
export type PromptItem = { id: string; title: string; prompt: string };
export type KitItem = { id: string; name: string; score: number };

export type ConnectorKind =
  | "hermes"
  | "gmail"
  | "slack"
  | "notion"
  | "sheets"
  | "webhook"
  | "custom"
  | string;

export type ConnectorItem = {
  id: string;
  kind: ConnectorKind;
  name: string;
  description: string;
  connected: boolean;
  baseUrl?: string;
};

export type McpTransport = "stdio" | "sse" | "http" | string;

export type McpServerItem = {
  id: string;
  name: string;
  transport: McpTransport;
  command?: string;
  args?: string;
  url?: string;
  enabled: boolean;
};

export type DiscoveryQuestion = {
  questionKey: string;
  content: string;
};

export type HealthInfo = {
  status: string;
  dbOk: boolean;
  providersReachable: boolean;
};

const mode = (import.meta.env.VITE_API_MODE as string) || "http";
const base = (import.meta.env.VITE_API_BASE as string) || "http://127.0.0.1:8000";

const TIER_LABEL: Record<string, string> = {
  TIER_1_CODE: "Rules",
  TIER_2_CLASSICAL_ML: "Smart match",
  TIER_3_LLM_AGENT: "AI writer",
};

const KIND_LABEL: Record<string, string> = {
  happy: "Smooth day",
  ambiguity: "Missing pieces",
  failure: "When things break",
  happy_path: "Smooth day",
  edge: "Missing pieces",
  error: "When things break",
};

function persistSession(session: SessionDraft | null) {
  storageSet("session", session);
}

function loadSession(): SessionDraft | null {
  return storageGet<SessionDraft | null>("session", null);
}

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const method = init?.method ?? "GET";
  logger.debug("http", `${method} ${path}`);
  try {
    const res = await fetch(`${base}${path}`, {
      headers: { "content-type": "application/json", ...(init?.headers || {}) },
      ...init,
    });
    if (!res.ok) {
      let detail = `${res.status} ${path}`;
      try {
        const body = await res.json();
        detail = body.detail ? String(body.detail) : detail;
      } catch {
        /* ignore */
      }
      logger.error("http", detail);
      throw new Error(detail);
    }
    if (res.status === 204) return undefined as T;
    return res.json() as Promise<T>;
  } catch (err) {
    logger.error("http", `Request failed ${path}`, { error: String(err) });
    throw err;
  }
}

export const apiClient = {
  mode: () => mode as "mock" | "http",
  baseUrl: () => base,

  async health(): Promise<HealthInfo> {
    const h = await http<{
      status: string;
      db_ok: boolean;
      providers_reachable: boolean;
    }>("/health");
    return {
      status: h.status,
      dbOk: h.db_ok,
      providersReachable: h.providers_reachable,
    };
  },

  async waitForApi(timeoutMs = 30000): Promise<HealthInfo> {
    const start = Date.now();
    let lastErr = "API not ready";
    while (Date.now() - start < timeoutMs) {
      try {
        const h = await this.health();
        if (h.dbOk) return h;
      } catch (e) {
        lastErr = String(e);
      }
      await new Promise((r) => setTimeout(r, 500));
    }
    throw new Error(lastErr);
  },

  async createSession(idea: string): Promise<SessionDraft> {
    const project = await http<{ id: string; name: string }>("/api/v1/projects", {
      method: "POST",
      body: JSON.stringify({
        name: idea.slice(0, 48) || "My helper",
        description: idea,
      }),
    });
    const session = await http<{
      id: string;
      project_id: string;
      stage: string;
      raw_user_prompt: string;
    }>("/api/v1/sessions", {
      method: "POST",
      body: JSON.stringify({ project_id: project.id, raw_user_prompt: idea }),
    });
    const draft: SessionDraft = {
      id: session.id,
      projectId: project.id,
      projectName: project.name,
      idea,
      stage: session.stage,
    };
    persistSession(draft);
    logger.info("session", "Session created", { id: draft.id });
    return draft;
  },

  getSession(): SessionDraft | null {
    return loadSession();
  },

  async refreshSession(): Promise<SessionDraft | null> {
    const cur = loadSession();
    if (!cur) return null;
    const session = await http<{
      id: string;
      project_id: string;
      stage: string;
      raw_user_prompt: string;
    }>(`/api/v1/sessions/${cur.id}`);
    const draft: SessionDraft = {
      id: session.id,
      projectId: session.project_id,
      projectName: cur.projectName,
      idea: session.raw_user_prompt,
      stage: session.stage,
    };
    persistSession(draft);
    return draft;
  },

  async startDiscovery(): Promise<DiscoveryQuestion[]> {
    const sid = loadSession()?.id;
    if (!sid) throw new Error("No session");
    const msgs = await http<
      { role: string; content: string; question_key: string | null }[]
    >(`/api/v1/discovery/${sid}/start`, { method: "POST" });
    const qs = msgs
      .filter((m) => m.role === "assistant" && m.question_key)
      .map((m) => ({
        questionKey: m.question_key as string,
        content: m.content,
      }));
    logger.info("studio", "Discovery started", { count: qs.length });
    return qs;
  },

  async answerDiscovery(questionKey: string, answer: string): Promise<void> {
    const sid = loadSession()?.id;
    if (!sid) throw new Error("No session");
    await http(`/api/v1/discovery/${sid}/answer`, {
      method: "POST",
      body: JSON.stringify({ question_key: questionKey, answer }),
    });
  },

  async finalizeDiscovery(): Promise<void> {
    const sid = loadSession()?.id;
    if (!sid) throw new Error("No session");
    await http(`/api/v1/discovery/${sid}/finalize`, {
      method: "POST",
      body: JSON.stringify({}),
    });
    await this.refreshSession();
    logger.info("studio", "Scope finalized");
  },

  async planPaths(): Promise<PlanPath[]> {
    const sid = loadSession()?.id;
    if (!sid) throw new Error("No session");
    const scenarios = await http<
      {
        id: string;
        kind: string;
        title: string;
        ascii_flow: string;
        steps: { processing_goal: string }[];
      }[]
    >(`/api/v1/flows/${sid}/generate`, { method: "POST" });
    logger.info("studio", "Flows generated", { count: scenarios.length });
    return scenarios.map((s) => ({
      id: s.id,
      kind: s.kind,
      title: KIND_LABEL[s.kind] || s.title,
      summary:
        s.steps?.[0]?.processing_goal ||
        s.ascii_flow ||
        s.title,
      asciiFlow: s.ascii_flow || s.title,
    }));
  },

  async approvePlan(): Promise<void> {
    const sid = loadSession()?.id;
    if (!sid) throw new Error("No session");
    await http(`/api/v1/flows/${sid}/approve`, { method: "POST" });
    await this.refreshSession();
    logger.info("studio", "Plan approved");
  },

  async roles(): Promise<RoleRow[]> {
    const sid = loadSession()?.id;
    if (!sid) throw new Error("No session");
    const alloc = await http<
      {
        step_name: string;
        description: string;
        allocated_tier: string;
        rationale: string;
      }[]
    >(`/api/v1/allocation/${sid}/run`, { method: "POST" });
    await http(`/api/v1/architecture/${sid}/build`, { method: "POST" });
    await this.refreshSession();
    logger.info("studio", "Allocation + architecture ready");
    return alloc.map((a) => ({
      name: a.step_name,
      tierLabel: TIER_LABEL[a.allocated_tier] || a.allocated_tier,
      blurb: a.rationale || a.description || "",
    }));
  },

  async buildKit(): Promise<CheckResult> {
    const sid = loadSession()?.id;
    if (!sid) throw new Error("No session");
    await http(`/api/v1/gates/${sid}/dry-run`, { method: "POST" });
    await http(`/api/v1/scaffold/${sid}/run`, {
      method: "POST",
      body: JSON.stringify({}),
    });
    const pkg = await http<{
      pytest_passed: boolean;
      zip_path: string | null;
      checksum_sha256: string | null;
      status: string;
      files: unknown[];
    }>(`/api/v1/package/${sid}/build`, {
      method: "POST",
      body: JSON.stringify({ run_verify: true }),
    });
    let overall = 0.7;
    let summary = "Package built";
    try {
      const sim = await http<{
        score: { overall: number };
        summary: string;
        status: string;
      }>(`/api/v1/simulate/${sid}/run`, {
        method: "POST",
        body: JSON.stringify({ include_all_scenarios: true }),
      });
      overall = sim.score?.overall ?? overall;
      summary = sim.summary || summary;
    } catch (e) {
      logger.warn("package", "Simulate skipped", { error: String(e) });
    }
    const check: CheckResult = {
      overall,
      packageOk: (pkg.files?.length ?? 0) > 0 || pkg.status === "ready",
      testsOk: Boolean(pkg.pytest_passed),
      zipOk: Boolean(pkg.zip_path && pkg.checksum_sha256),
      summary,
    };
    storageSet("check", check);
    await this.refreshSession();
    logger.info("package", "Kit built", { score: check.overall });
    return check;
  },

  getCheck(): CheckResult | null {
    return storageGet<CheckResult | null>("check", null);
  },

  async edgeCases(): Promise<EdgeItem[]> {
    const sid = loadSession()?.id;
    if (!sid) throw new Error("No session");
    let edges = await http<
      { id: string; title: string; description: string; expected_behavior: string }[]
    >(`/api/v1/edge-cases/${sid}`);
    if (!edges.length) {
      edges = await http(`/api/v1/edge-cases/${sid}/generate`, {
        method: "POST",
        body: JSON.stringify({ count: 4 }),
      });
    }
    return edges.map((e) => ({
      id: e.id,
      title: e.title,
      detail: e.description || e.expected_behavior || "",
    }));
  },

  async codingPrompts(): Promise<PromptItem[]> {
    const sid = loadSession()?.id;
    if (!sid) throw new Error("No session");
    let prompts = await http<
      { id: string; title: string; prompt_text: string }[]
    >(`/api/v1/prompts/${sid}`);
    if (!prompts.length) {
      prompts = await http(`/api/v1/prompts/${sid}/generate`, {
        method: "POST",
        body: JSON.stringify({ tool_target: "cursor" }),
      });
    }
    return prompts.map((p) => ({
      id: p.id,
      title: p.title,
      prompt: p.prompt_text,
    }));
  },

  async iterateImprove(): Promise<{ notes: string; scoreAfter: number | null }> {
    const sid = loadSession()?.id;
    if (!sid) throw new Error("No session");
    const it = await http<{
      notes: string;
      score_after: number | null;
    }>(`/api/v1/improve/${sid}/iterate`, {
      method: "POST",
      body: JSON.stringify({
        auto_attach_edge_cases: true,
        generate_prompts: true,
      }),
    });
    logger.info("improve", "Iteration complete", {
      score: it.score_after,
    });
    return { notes: it.notes, scoreAfter: it.score_after };
  },

  async saveKit(name: string): Promise<KitItem> {
    const sid = loadSession()?.id;
    if (!sid) throw new Error("No session");
    const pack = await http<{ id: string; name: string; best_score: number }>(
      `/api/v1/improve/${sid}/publish-local`,
      {
        method: "POST",
        body: JSON.stringify({ name }),
      },
    );
    const kit = { id: pack.id, name: pack.name, score: pack.best_score };
    logger.info("kits", "Kit saved", { id: kit.id });
    return kit;
  },

  async listKits(): Promise<KitItem[]> {
    const packs = await http<{ id: string; name: string; best_score: number }[]>(
      "/api/v1/packs",
    );
    return packs.map((p) => ({
      id: p.id,
      name: p.name,
      score: p.best_score,
    }));
  },

  async forkKit(packId: string): Promise<SessionDraft> {
    const session = await http<{
      id: string;
      project_id: string;
      stage: string;
      raw_user_prompt: string;
    }>(`/api/v1/packs/${packId}/fork`, {
      method: "POST",
      body: JSON.stringify({}),
    });
    const draft: SessionDraft = {
      id: session.id,
      projectId: session.project_id,
      projectName: "Forked kit",
      idea: session.raw_user_prompt,
      stage: session.stage,
    };
    persistSession(draft);
    logger.info("kits", "Kit forked", { packId, sessionId: draft.id });
    return draft;
  },

  async activateLicense(key: string): Promise<{ ok: boolean; message: string }> {
    try {
      await http("/api/v1/license/activate", {
        method: "POST",
        body: JSON.stringify({ license_key: key }),
      });
      return { ok: true, message: "Pro unlocked" };
    } catch {
      return { ok: false, message: "Could not activate" };
    }
  },

  async licenseStatus(): Promise<{
    tier: string;
    status: string;
    features: string[];
  }> {
    return http("/api/v1/license");
  },

  async getSettings(): Promise<Record<string, unknown>> {
    return http("/api/v1/settings");
  },

  async putSettings(patch: Record<string, unknown>): Promise<void> {
    await http("/api/v1/settings", {
      method: "PUT",
      body: JSON.stringify(patch),
    });
    logger.info("settings", "Settings updated", { keys: Object.keys(patch) });
  },

  async listProviders(): Promise<
    { id: string; name: string; enabled: boolean; default_model: string }[]
  > {
    return http("/api/v1/providers");
  },

  async testProvider(id: string): Promise<{ ok: boolean; message: string; latency_ms?: number }> {
    return http(`/api/v1/providers/${id}/test`, { method: "POST" });
  },

  async listConnectors(): Promise<ConnectorItem[]> {
    return http("/api/v1/connectors");
  },

  async setConnectorConnected(
    id: string,
    connected: boolean,
  ): Promise<ConnectorItem> {
    const updated = await http<ConnectorItem>(`/api/v1/connectors/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ connected }),
    });
    logger.info(
      "connectors",
      connected ? `${updated.name} connected` : `${updated.name} disconnected`,
    );
    return updated;
  },

  async addCustomConnector(input: {
    name: string;
    baseUrl: string;
  }): Promise<ConnectorItem> {
    return http("/api/v1/connectors", {
      method: "POST",
      body: JSON.stringify({
        kind: "custom",
        name: input.name,
        base_url: input.baseUrl,
      }),
    });
  },

  async testConnector(id: string): Promise<{ ok: boolean; message: string }> {
    return http(`/api/v1/connectors/${id}/test`, { method: "POST" });
  },

  async listMcpServers(): Promise<McpServerItem[]> {
    return http("/api/v1/mcp/servers");
  },

  async setMcpEnabled(id: string, enabled: boolean): Promise<McpServerItem> {
    return http(`/api/v1/mcp/servers/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ enabled }),
    });
  },

  async addMcpServer(input: {
    name: string;
    transport: McpTransport;
    command?: string;
    args?: string;
    url?: string;
  }): Promise<McpServerItem> {
    return http("/api/v1/mcp/servers", {
      method: "POST",
      body: JSON.stringify(input),
    });
  },

  async removeMcpServer(id: string): Promise<void> {
    await http(`/api/v1/mcp/servers/${id}`, { method: "DELETE" });
  },

  async testMcpServer(id: string): Promise<{ ok: boolean; message: string }> {
    return http(`/api/v1/mcp/servers/${id}/test`, { method: "POST" });
  },
};
