const PREFIX = "mas.";

export function storageGet<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(PREFIX + key);
    if (raw == null) return fallback;
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

export function storageSet<T>(key: string, value: T): void {
  try {
    localStorage.setItem(PREFIX + key, JSON.stringify(value));
  } catch {
    /* quota / private mode */
  }
}

export function storageRemove(key: string): void {
  try {
    localStorage.removeItem(PREFIX + key);
  } catch {
    /* ignore */
  }
}

/** Migrate legacy unprefixed keys once. */
export function migrateLegacyKey(legacy: string, next: string): void {
  try {
    if (localStorage.getItem(PREFIX + next) != null) return;
    const raw = localStorage.getItem(legacy);
    if (raw == null) return;
    localStorage.setItem(PREFIX + next, raw);
  } catch {
    /* ignore */
  }
}
