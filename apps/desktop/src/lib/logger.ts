import { storageGet, storageSet } from "./storage";

export type LogLevel = "debug" | "info" | "warn" | "error";

export type LogEntry = {
  id: string;
  ts: string;
  level: LogLevel;
  source: string;
  message: string;
  data?: Record<string, unknown>;
};

const MAX_LOGS = 200;
const KEY = "activity_log";

type Listener = () => void;

let entries: LogEntry[] = storageGet<LogEntry[]>(KEY, []);
const listeners = new Set<Listener>();

function emit() {
  storageSet(KEY, entries);
  listeners.forEach((l) => l());
}

function push(entry: LogEntry) {
  entries = [entry, ...entries].slice(0, MAX_LOGS);
  const line = `[${entry.level}] ${entry.source}: ${entry.message}`;
  if (entry.level === "error") console.error(line, entry.data ?? "");
  else if (entry.level === "warn") console.warn(line, entry.data ?? "");
  else if (entry.level === "debug") console.debug(line, entry.data ?? "");
  else console.info(line, entry.data ?? "");
  emit();
}

function make(
  level: LogLevel,
  source: string,
  message: string,
  data?: Record<string, unknown>,
): LogEntry {
  return {
    id: `log_${Date.now().toString(16)}_${Math.random().toString(16).slice(2, 6)}`,
    ts: new Date().toISOString(),
    level,
    source,
    message,
    data,
  };
}

export const logger = {
  debug(source: string, message: string, data?: Record<string, unknown>) {
    push(make("debug", source, message, data));
  },
  info(source: string, message: string, data?: Record<string, unknown>) {
    push(make("info", source, message, data));
  },
  warn(source: string, message: string, data?: Record<string, unknown>) {
    push(make("warn", source, message, data));
  },
  error(source: string, message: string, data?: Record<string, unknown>) {
    push(make("error", source, message, data));
  },
  list(): LogEntry[] {
    return entries;
  },
  clear() {
    entries = [];
    emit();
    console.info("[info] logger: activity log cleared");
  },
  subscribe(listener: Listener): () => void {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },
  getSnapshot(): LogEntry[] {
    return entries;
  },
};

logger.info("app", "Studio session restored", { logCount: entries.length });
