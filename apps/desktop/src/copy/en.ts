export const copy = {
  brand: "MetaAgent Studio",
  tagline: "Turn an idea into a working helper",
  statusReady: "Ready",
  statusThinking: "Thinking…",
  nav: {
    home: "Start",
    studio: "Build my agent",
    check: "Make sure it works",
    improve: "Make it better",
    kits: "My saved kits",
    settings: "Settings",
  },
  home: {
    support: "Describe what you want. We’ll guide the rest.",
    placeholder: "Example: Sort support emails and draft kind replies…",
    cta: "Start building",
    examples: [
      "Help with support emails",
      "Read invoices safely",
      "Summarize research notes",
    ],
  },
  studio: {
    steps: [
      "Your idea",
      "A few questions",
      "Approve the plan",
      "Who does what",
      "Build the kit",
    ],
    next: "Continue",
    back: "Back",
    approve: "Looks good",
    paths: {
      happy: "Smooth day",
      ambiguity: "Missing pieces",
      failure: "When things break",
    },
    tiers: {
      t1: "Rules",
      t2: "Smart match",
      t3: "AI writer",
    },
    buildCta: "Build kit & check",
  },
  check: {
    title: "Make sure it works",
    empty: "Build a kit first from Build my agent.",
    score: "Overall score",
    packageOk: "Files written",
    testsOk: "Checks ran",
    zipOk: "Zip ready",
    improve: "Make it better",
    save: "Save kit",
  },
  improve: {
    title: "Make it better",
    edges: "Tricky situations",
    prompts: "Ask a coding helper",
    copyPrompt: "Copy prompt",
    iterate: "Try another improvement",
  },
  kits: {
    title: "My saved kits",
    empty: "No kits yet — build one from Start.",
    fork: "Reuse",
    open: "Open",
  },
  settings: {
    title: "Settings",
    license: "License key",
    activate: "Activate",
    brain: "Brain",
    local: "Local",
    cloud: "Cloud",
    export: "Save finished kits to",
    developer: "Developer",
    greet: "Test Rust bridge",
  },
  pathsAscii: {
    happy: "Check input → Find notes → Write reply → Send safely",
    ambiguity: "Check input → Ask what’s missing → Wait",
    failure: "Check input → Service busy → Queue & retry",
  },
} as const;

export type ViewId =
  | "home"
  | "studio"
  | "check"
  | "improve"
  | "kits"
  | "settings";
