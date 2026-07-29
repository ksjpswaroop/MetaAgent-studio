import { useSyncExternalStore } from "react";
import { appState } from "../lib/appState";

export function useAppState() {
  return useSyncExternalStore(appState.subscribe, appState.getSnapshot);
}
