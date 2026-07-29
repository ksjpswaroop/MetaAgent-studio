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

const mode = (import.meta.env.VITE_API_MODE as string) || "mock";
const base = (import.meta.env.VITE_API_BASE as string) || "http://127.0.0.1:8000";

const memory = {
  session: null as SessionDraft | null,
  kits: [] as KitItem[],
  check: null as CheckResult | null,
};

function uid(prefix: string) {
  return `${prefix}_${Math.random().toString(16).slice(2, 10)}`;
}

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${base}${path}`, {
    headers: { "content-type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!res.ok) throw new Error(`${res.status} ${path}`);
  return res.json() as Promise<T>;
}

export const apiClient = {
  mode: () => mode as "mock" | "http",

  async createSession(idea: string): Promise<SessionDraft> {
    if (mode === "http") {
      const project = await http<{ id: string; name: string }>("/api/v1/projects", {
        method: "POST",
        body: JSON.stringify({ name: idea.slice(0, 40) || "My helper", description: idea }),
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
      return memory.session;
    }
    memory.session = {
      id: uid("sess"),
      projectName: idea.slice(0, 40) || "My helper",
      idea,
      stage: "created",
    };
    return memory.session;
  },

  getSession(): SessionDraft | null {
    return memory.session;
  },

  async discoveryQuestions(): Promise<string[]> {
    return [
      "When should this helper wake up? (message arrives / on a schedule / when you ask)",
      "What outside tools does it need?",
      "Should a person approve before it sends anything?",
      "If a tool is busy, what should happen?",
    ];
  },

  async planPaths(): Promise<PlanPath[]> {
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
      // Placeholder: real wiring maps to package + simulate endpoints
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
    if (memory.session) memory.session.stage = "scaffolded";
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
    memory.kits.unshift(kit);
    try {
      localStorage.setItem("mas_kits", JSON.stringify(memory.kits));
    } catch {
      /* ignore */
    }
    return kit;
  },

  listKits(): KitItem[] {
    if (!memory.kits.length) {
      try {
        memory.kits = JSON.parse(localStorage.getItem("mas_kits") || "[]");
      } catch {
        memory.kits = [];
      }
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
        return { ok: true, message: "Pro unlocked" };
      } catch {
        return { ok: false, message: "Could not activate" };
      }
    }
    const ok = /^MAS-PRO-/i.test(key.trim());
    return { ok, message: ok ? "Pro unlocked (mock)" : "Use MAS-PRO-XXXX-XXXX-XXXX" };
  },
};
