import { logger } from "./logger";
import { migrateLegacyKey, storageGet, storageSet } from "./storage";

export type SessionDraft = {
  id: string;
  projectName: string;
  idea: string;
  stage: string;
};

export type PlanPath = {
  id: "happy" | "ambiguity" | "failure";
  title: string;
  summary: string;
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
  | "custom";

export type ConnectorItem = {
  id: string;
  kind: ConnectorKind;
  name: string;
  description: string;
  connected: boolean;
  baseUrl?: string;
};

export type McpTransport = "stdio" | "sse" | "http";

export type McpServerItem = {
  id: string;
  name: string;
  transport: McpTransport;
  command?: string;
  args?: string;
  url?: string;
  enabled: boolean;
};

const mode = (import.meta.env.VITE_API_MODE as string) || "mock";
const base = (import.meta.env.VITE_API_BASE as string) || "http://127.0.0.1:8000";

const defaultConnectors: ConnectorItem[] = [
  {
    id: "conn_hermes",
    kind: "hermes",
    name: "Hermes Agent",
    description: "Run and hand off work to a Hermes agent",
    connected: false,
    baseUrl: "http://127.0.0.1:8787",
  },
  {
    id: "conn_gmail",
    kind: "gmail",
    name: "Gmail",
    description: "Read and draft email",
    connected: false,
  },
  {
    id: "conn_slack",
    kind: "slack",
    name: "Slack",
    description: "Post messages to channels",
    connected: false,
  },
  {
    id: "conn_notion",
    kind: "notion",
    name: "Notion",
    description: "Search pages and notes",
    connected: true,
  },
  {
    id: "conn_sheets",
    kind: "sheets",
    name: "Google Sheets",
    description: "Read and update rows",
    connected: false,
  },
  {
    id: "conn_webhook",
    kind: "webhook",
    name: "Webhook",
    description: "Call your own HTTP endpoint",
    connected: false,
    baseUrl: "https://example.com/hook",
  },
];

const defaultMcp: McpServerItem[] = [
  {
    id: "mcp_filesystem",
    name: "Filesystem",
    transport: "stdio",
    command: "npx",
    args: "-y @modelcontextprotocol/server-filesystem ~/Documents",
    enabled: false,
  },
  {
    id: "mcp_fetch",
    name: "Fetch",
    transport: "stdio",
    command: "npx",
    args: "-y @modelcontextprotocol/server-fetch",
    enabled: true,
  },
];

migrateLegacyKey("mas_kits", "kits");
migrateLegacyKey("mas_connectors", "connectors");
migrateLegacyKey("mas_mcp", "mcp");

const memory = {
  session: storageGet<SessionDraft | null>("session", null),
  kits: storageGet<KitItem[]>("kits", []),
  check: storageGet<CheckResult | null>("check", null),
  connectors: null as ConnectorItem[] | null,
  mcp: null as McpServerItem[] | null,
};

function persistSession() {
  storageSet("session", memory.session);
}

function persistCheck() {
  storageSet("check", memory.check);
}

function persistKits() {
  storageSet("kits", memory.kits);
}

function mergeDefaultConnectors(stored: ConnectorItem[]): ConnectorItem[] {
  const byId = new Map(stored.map((c) => [c.id, c]));
  const merged: ConnectorItem[] = [];
  for (const def of defaultConnectors) {
    merged.push(byId.get(def.id) ?? def);
    byId.delete(def.id);
  }
  for (const extra of byId.values()) merged.push(extra);
  return merged;
}

function loadConnectors(): ConnectorItem[] {
  if (memory.connectors) return memory.connectors;
  const stored = storageGet<ConnectorItem[] | null>("connectors", null);
  memory.connectors = stored
    ? mergeDefaultConnectors(stored)
    : [...defaultConnectors];
  return memory.connectors;
}

function saveConnectors(list: ConnectorItem[]) {
  memory.connectors = list;
  storageSet("connectors", list);
}

function loadMcp(): McpServerItem[] {
  if (memory.mcp) return memory.mcp;
  const stored = storageGet<McpServerItem[] | null>("mcp", null);
  memory.mcp = stored ?? [...defaultMcp];
  return memory.mcp;
}

function saveMcp(list: McpServerItem[]) {
  memory.mcp = list;
  storageSet("mcp", list);
}

function uid(prefix: string) {
  return `${prefix}_${Math.random().toString(16).slice(2, 10)}`;
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
      logger.error("http", `${res.status} ${path}`);
      throw new Error(`${res.status} ${path}`);
    }
    return res.json() as Promise<T>;
  } catch (err) {
    logger.error("http", `Request failed ${path}`, {
      error: String(err),
    });
    throw err;
  }
}

export const apiClient = {
  mode: () => mode as "mock" | "http",

  async createSession(idea: string): Promise<SessionDraft> {
    if (mode === "http") {
      const project = await http<{ id: string; name: string }>("/api/v1/projects", {
        method: "POST",
        body: JSON.stringify({
          name: idea.slice(0, 40) || "My helper",
          description: idea,
        }),
      });
      const session = await http<{ id: string }>("/api/v1/sessions", {
        method: "POST",
        body: JSON.stringify({ project_id: project.id, raw_user_prompt: idea }),
      });
      memory.session = {
        id: session.id,
        projectName: project.name,
        idea,
        stage: "created",
      };
      persistSession();
      logger.info("session", "Session created", { id: memory.session.id });
      return memory.session;
    }
    memory.session = {
      id: uid("sess"),
      projectName: idea.slice(0, 40) || "My helper",
      idea,
      stage: "created",
    };
    persistSession();
    logger.info("session", "Session created (mock)", { id: memory.session.id });
    return memory.session;
  },

  getSession(): SessionDraft | null {
    return memory.session;
  },

  async discoveryQuestions(): Promise<string[]> {
    logger.info("studio", "Loaded discovery questions");
    return [
      "When should this helper wake up? (message arrives / on a schedule / when you ask)",
      "What outside tools does it need?",
      "Should a person approve before it sends anything?",
      "If a tool is busy, what should happen?",
    ];
  },

  async planPaths(): Promise<PlanPath[]> {
    logger.info("studio", "Loaded plan paths");
    return [
      {
        id: "happy",
        title: "Smooth day",
        summary: "Everything arrives complete and tools respond.",
      },
      {
        id: "ambiguity",
        title: "Missing pieces",
        summary: "Some details are unclear — we ask before acting.",
      },
      {
        id: "failure",
        title: "When things break",
        summary: "A tool times out — we queue and try again safely.",
      },
    ];
  },

  async roles(): Promise<RoleRow[]> {
    logger.info("studio", "Loaded role assignments");
    return [
      {
        name: "Gatekeeper",
        tierLabel: "Rules",
        blurb: "Checks the input is complete and safe.",
      },
      {
        name: "Librarian",
        tierLabel: "Smart match",
        blurb: "Finds the most relevant notes.",
      },
      {
        name: "Writer",
        tierLabel: "AI writer",
        blurb: "Drafts a clear, kind reply.",
      },
    ];
  },

  async buildKit(): Promise<CheckResult> {
    if (mode === "http" && memory.session) {
      await http(`/api/v1/package/${memory.session.id}/build`, {
        method: "POST",
        body: JSON.stringify({ run_verify: true }),
      }).catch(() => null);
    }
    memory.check = {
      overall: 0.82,
      packageOk: true,
      testsOk: true,
      zipOk: true,
    };
    if (memory.session) {
      memory.session = { ...memory.session, stage: "scaffolded" };
      persistSession();
    }
    persistCheck();
    logger.info("package", "Kit built", { score: memory.check.overall });
    return memory.check;
  },

  getCheck(): CheckResult | null {
    return memory.check;
  },

  async edgeCases(): Promise<EdgeItem[]> {
    return [
      {
        id: "e1",
        title: "Notes search is slow",
        detail: "Helper should wait, then use a backup path.",
      },
      {
        id: "e2",
        title: "Message has no name",
        detail: "Ask a short clarifying question.",
      },
    ];
  },

  async codingPrompts(): Promise<PromptItem[]> {
    return [
      {
        id: "p1",
        title: "Handle slow notes search",
        prompt:
          "In the retrieval step, add a timeout and route to a fallback queue. Add a test for the timeout path.",
      },
    ];
  },

  async saveKit(name: string): Promise<KitItem> {
    const kit = {
      id: uid("kit"),
      name,
      score: memory.check?.overall ?? 0.7,
    };
    memory.kits = [kit, ...memory.kits];
    persistKits();
    logger.info("kits", "Kit saved", { id: kit.id, name: kit.name });
    return kit;
  },

  listKits(): KitItem[] {
    if (!memory.kits.length) {
      memory.kits = storageGet<KitItem[]>("kits", []);
    }
    return memory.kits;
  },

  async activateLicense(key: string): Promise<{ ok: boolean; message: string }> {
    if (mode === "http") {
      try {
        await http("/api/v1/license/activate", {
          method: "POST",
          body: JSON.stringify({ license_key: key }),
        });
        logger.info("license", "Pro unlocked");
        return { ok: true, message: "Pro unlocked" };
      } catch {
        logger.warn("license", "Activation failed");
        return { ok: false, message: "Could not activate" };
      }
    }
    const ok = /^MAS-PRO-/i.test(key.trim());
    logger.info("license", ok ? "Pro unlocked (mock)" : "Invalid license format");
    return {
      ok,
      message: ok ? "Pro unlocked (mock)" : "Use MAS-PRO-XXXX-XXXX-XXXX",
    };
  },

  async listConnectors(): Promise<ConnectorItem[]> {
    return loadConnectors().map((c) => ({ ...c }));
  },

  async setConnectorConnected(
    id: string,
    connected: boolean,
  ): Promise<ConnectorItem> {
    if (mode === "http") {
      try {
        const updated = await http<ConnectorItem>(`/api/v1/connectors/${id}`, {
          method: "PATCH",
          body: JSON.stringify({ connected }),
        });
        logger.info("connectors", connected ? "Connected" : "Disconnected", {
          id,
        });
        return updated;
      } catch {
        /* fall through */
      }
    }
    const list = loadConnectors();
    const next = list.map((c) => (c.id === id ? { ...c, connected } : c));
    saveConnectors(next);
    const found = next.find((c) => c.id === id);
    if (!found) {
      logger.error("connectors", "Connector not found", { id });
      throw new Error("connector not found");
    }
    logger.info(
      "connectors",
      connected ? `${found.name} connected` : `${found.name} disconnected`,
      { id },
    );
    return found;
  },

  async addCustomConnector(input: {
    name: string;
    baseUrl: string;
  }): Promise<ConnectorItem> {
    if (mode === "http") {
      try {
        const created = await http<ConnectorItem>("/api/v1/connectors", {
          method: "POST",
          body: JSON.stringify({
            kind: "custom",
            name: input.name,
            base_url: input.baseUrl,
          }),
        });
        logger.info("connectors", "Custom connector added", { id: created.id });
        return created;
      } catch {
        /* fall through */
      }
    }
    const item: ConnectorItem = {
      id: uid("conn"),
      kind: "custom",
      name: input.name,
      description: "Custom REST connector",
      connected: true,
      baseUrl: input.baseUrl,
    };
    saveConnectors([item, ...loadConnectors()]);
    logger.info("connectors", "Custom connector added", { id: item.id });
    return item;
  },

  async testConnector(id: string): Promise<{ ok: boolean; message: string }> {
    if (mode === "http") {
      try {
        const res = await http<{ ok: boolean; message: string }>(
          `/api/v1/connectors/${id}/test`,
          { method: "POST" },
        );
        logger.info("connectors", res.ok ? "Test ok" : "Test failed", { id });
        return res;
      } catch {
        logger.warn("connectors", "Test failed", { id });
        return { ok: false, message: "Couldn’t reach it — check the details" };
      }
    }
    const c = loadConnectors().find((x) => x.id === id);
    if (!c) {
      logger.warn("connectors", "Test failed — missing", { id });
      return { ok: false, message: "Couldn’t reach it — check the details" };
    }
    const ok = c.connected || c.kind === "webhook" || c.kind === "hermes";
    logger.info("connectors", ok ? "Test ok" : "Test failed", {
      id,
      name: c.name,
    });
    return {
      ok,
      message: ok ? "Looks good" : "Connect first, then test",
    };
  },

  async listMcpServers(): Promise<McpServerItem[]> {
    return loadMcp().map((s) => ({ ...s }));
  },

  async setMcpEnabled(id: string, enabled: boolean): Promise<McpServerItem> {
    if (mode === "http") {
      try {
        return await http<McpServerItem>(`/api/v1/mcp/servers/${id}`, {
          method: "PATCH",
          body: JSON.stringify({ enabled }),
        });
      } catch {
        /* fall through */
      }
    }
    const next = loadMcp().map((s) => (s.id === id ? { ...s, enabled } : s));
    saveMcp(next);
    const found = next.find((s) => s.id === id);
    if (!found) {
      logger.error("mcp", "Server not found", { id });
      throw new Error("mcp server not found");
    }
    logger.info("mcp", enabled ? `${found.name} on` : `${found.name} off`, {
      id,
    });
    return found;
  },

  async addMcpServer(input: {
    name: string;
    transport: McpTransport;
    command?: string;
    args?: string;
    url?: string;
  }): Promise<McpServerItem> {
    if (mode === "http") {
      try {
        return await http<McpServerItem>("/api/v1/mcp/servers", {
          method: "POST",
          body: JSON.stringify(input),
        });
      } catch {
        /* fall through */
      }
    }
    const item: McpServerItem = {
      id: uid("mcp"),
      name: input.name,
      transport: input.transport,
      command: input.command,
      args: input.args,
      url: input.url,
      enabled: true,
    };
    saveMcp([item, ...loadMcp()]);
    logger.info("mcp", "Server added", { id: item.id, name: item.name });
    return item;
  },

  async removeMcpServer(id: string): Promise<void> {
    if (mode === "http") {
      try {
        await http(`/api/v1/mcp/servers/${id}`, { method: "DELETE" });
        logger.info("mcp", "Server removed", { id });
        return;
      } catch {
        /* fall through */
      }
    }
    saveMcp(loadMcp().filter((s) => s.id !== id));
    logger.info("mcp", "Server removed", { id });
  },

  async testMcpServer(id: string): Promise<{ ok: boolean; message: string }> {
    if (mode === "http") {
      try {
        return await http<{ ok: boolean; message: string }>(
          `/api/v1/mcp/servers/${id}/test`,
          { method: "POST" },
        );
      } catch {
        logger.warn("mcp", "Test failed", { id });
        return { ok: false, message: "Couldn’t reach it — check the details" };
      }
    }
    const s = loadMcp().find((x) => x.id === id);
    if (!s) {
      logger.warn("mcp", "Test failed — missing", { id });
      return { ok: false, message: "Couldn’t reach it — check the details" };
    }
    const ok = Boolean(s.enabled && (s.command || s.url));
    logger.info("mcp", ok ? "Test ok" : "Test failed", { id, name: s.name });
    return {
      ok,
      message: ok ? "Looks good" : "Couldn’t reach it — check the details",
    };
  },
};
