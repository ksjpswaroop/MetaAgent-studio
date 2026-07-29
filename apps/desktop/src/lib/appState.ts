import type { ViewId } from "../copy/en";
import { logger } from "./logger";
import { storageGet, storageSet } from "./storage";

export type StudioWizardState = {
  step: number;
  answers: string[];
  qIndex: number;
  activePath: "happy" | "ambiguity" | "failure";
};

export type SettingsState = {
  brain: "local" | "cloud";
  exportPath: string;
  licenseKey: string;
};

export type PersistedUiState = {
  view: ViewId;
  idea: string;
  studio: StudioWizardState;
  settings: SettingsState;
};

const KEY = "ui_state";
const VIEWS: ViewId[] = [
  "home",
  "studio",
  "check",
  "improve",
  "kits",
  "connections",
  "settings",
];

const defaultStudio: StudioWizardState = {
  step: 0,
  answers: [],
  qIndex: 0,
  activePath: "happy",
};

const defaultSettings: SettingsState = {
  brain: "local",
  exportPath: "~/MetaAgentExports",
  licenseKey: "",
};

function defaultState(): PersistedUiState {
  return {
    view: "home",
    idea: "",
    studio: { ...defaultStudio },
    settings: { ...defaultSettings },
  };
}

function normalize(raw: Partial<PersistedUiState> | null): PersistedUiState {
  const base = defaultState();
  if (!raw) return base;
  const view = VIEWS.includes(raw.view as ViewId) ? (raw.view as ViewId) : "home";
  return {
    view,
    idea: typeof raw.idea === "string" ? raw.idea : "",
    studio: {
      ...defaultStudio,
      ...(raw.studio ?? {}),
      answers: Array.isArray(raw.studio?.answers) ? raw.studio!.answers : [],
    },
    settings: {
      ...defaultSettings,
      ...(raw.settings ?? {}),
      brain: raw.settings?.brain === "cloud" ? "cloud" : "local",
    },
  };
}

type Listener = () => void;

let state: PersistedUiState = normalize(storageGet<Partial<PersistedUiState> | null>(KEY, null));
const listeners = new Set<Listener>();

function persist() {
  storageSet(KEY, state);
  listeners.forEach((l) => l());
}

export const appState = {
  get(): PersistedUiState {
    return state;
  },
  getSnapshot(): PersistedUiState {
    return state;
  },
  subscribe(listener: Listener): () => void {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },
  setView(view: ViewId) {
    if (state.view === view) return;
    state = { ...state, view };
    persist();
    logger.info("nav", `Opened ${view}`);
  },
  setIdea(idea: string) {
    state = { ...state, idea };
    persist();
  },
  patchStudio(patch: Partial<StudioWizardState>) {
    state = { ...state, studio: { ...state.studio, ...patch } };
    persist();
  },
  resetStudio() {
    state = { ...state, studio: { ...defaultStudio } };
    persist();
    logger.info("studio", "Wizard reset");
  },
  patchSettings(patch: Partial<SettingsState>) {
    state = { ...state, settings: { ...state.settings, ...patch } };
    persist();
    logger.info("settings", "Settings updated", { keys: Object.keys(patch) });
  },
};
