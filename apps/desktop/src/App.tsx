import { useState } from "react";
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

  async function handleStart(nextIdea: string) {
    setStatus(copy.statusThinking);
    logger.info("home", "Starting build from idea");
    await apiClient.createSession(nextIdea);
    appState.setIdea(nextIdea);
    appState.resetStudio();
    setStatus(copy.statusReady);
    appState.setView("studio");
  }

  async function handleSaveKit() {
    const session = apiClient.getSession();
    const name = session?.projectName || "My kit";
    setStatus(copy.statusThinking);
    await apiClient.saveKit(name);
    setKitsTick((t) => t + 1);
    setStatus(copy.statusReady);
    appState.setView("kits");
  }

  return (
    <AppShell
      view={ui.view}
      status={status}
      onNavigate={(v) => appState.setView(v)}
    >
      {ui.view === "home" && <HomeView onStart={handleStart} />}
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
      {ui.view === "improve" && <ImproveView />}
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
