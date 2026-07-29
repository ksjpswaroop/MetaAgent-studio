import { useEffect, useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import { AppShell } from "./components/shell/AppShell";
import { copy } from "./copy/en";
import { useAppState } from "./hooks/useAppState";
import { apiClient } from "./lib/apiClient";
import { appState } from "./lib/appState";
import { logger } from "./lib/logger";
import { CheckView } from "./views/CheckView";
import { ConnectionsView } from "./views/ConnectionsView";
import { HomeView } from "./views/HomeView";
import { ImproveView } from "./views/ImproveView";
import { KitsView } from "./views/KitsView";
import { SettingsView } from "./views/SettingsView";
import { StudioView } from "./views/StudioView";

export default function App() {
  const ui = useAppState();
  const [status, setStatus] = useState<string>(copy.statusReady);
  const [kitsTick, setKitsTick] = useState(0);
  const [apiReady, setApiReady] = useState(false);
  const [brainOnline, setBrainOnline] = useState(false);
  const [bootError, setBootError] = useState("");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setStatus(copy.statusThinking);
      try {
        try {
          await invoke("start_api");
        } catch {
          /* browser/dev without Tauri command */
        }
        const health = await apiClient.waitForApi(45000);
        if (cancelled) return;
        setApiReady(true);
        setBrainOnline(health.providersReachable);
        setStatus(
          health.providersReachable ? copy.statusReady : "Brain offline",
        );
        logger.info("app", "API ready", {
          providersReachable: health.providersReachable,
        });
      } catch (e) {
        if (cancelled) return;
        setBootError(String(e));
        setStatus("API offline");
        logger.error("app", "API boot failed", { error: String(e) });
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleStart(nextIdea: string) {
    if (!apiReady) {
      setBootError("API is still starting — wait a moment.");
      return;
    }
    setStatus(copy.statusThinking);
    logger.info("home", "Starting build from idea");
    try {
      await apiClient.createSession(nextIdea);
      appState.setIdea(nextIdea);
      appState.resetStudio();
      setStatus(brainOnline ? copy.statusReady : "Brain offline");
      appState.setView("studio");
    } catch (e) {
      setBootError(String(e));
      setStatus(copy.statusReady);
    }
  }

  async function handleSaveKit() {
    const session = apiClient.getSession();
    const name = session?.projectName || "My kit";
    setStatus(copy.statusThinking);
    try {
      await apiClient.saveKit(name);
      setKitsTick((t) => t + 1);
      appState.setView("kits");
    } catch (e) {
      setBootError(String(e));
    } finally {
      setStatus(copy.statusReady);
    }
  }

  return (
    <AppShell
      view={ui.view}
      status={status}
      onNavigate={(v) => appState.setView(v)}
    >
      {bootError && ui.view === "home" && (
        <p className="mb-4 text-sm text-[var(--li-warn)]">{bootError}</p>
      )}
      {ui.view === "home" && (
        <HomeView onStart={handleStart} disabled={!apiReady} />
      )}
      {ui.view === "studio" && (
        <StudioView
          idea={ui.idea || apiClient.getSession()?.idea || ""}
          onBuilt={() => appState.setView("check")}
          setStatus={setStatus}
        />
      )}
      {ui.view === "check" && (
        <CheckView
          onImprove={() => appState.setView("improve")}
          onSave={handleSaveKit}
        />
      )}
      {ui.view === "improve" && <ImproveView setStatus={setStatus} />}
      {ui.view === "kits" && (
        <KitsView
          key={kitsTick}
          onOpenStudio={() => appState.setView("studio")}
        />
      )}
      {ui.view === "connections" && (
        <ConnectionsView setStatus={setStatus} />
      )}
      {ui.view === "settings" && <SettingsView />}
    </AppShell>
  );
}
