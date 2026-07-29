import { useSyncExternalStore } from "react";
import { logger } from "../lib/logger";

export function useActivityLog() {
  return useSyncExternalStore(logger.subscribe, logger.getSnapshot);
}
