import { useState } from "react";
import { AppShell } from "./components/shell/AppShell";
import { copy, type ViewId } from "./copy/en";
import { apiClient } from "./lib/apiClient";
import { CheckView } from "./views/CheckView";
import { ConnectionsView } from "./views/ConnectionsView";
import { HomeView } from "./views/HomeView";
import { ImproveView } from "./views/ImproveView";
import { KitsView } from "./views/KitsView";
import { SettingsView } from "./views/SettingsView";
import { StudioView } from "./views/StudioView";

export default function App() {
  const [view, setView] = useState<ViewId>("home");
  const [status, setStatus] = useState<string>(copy.statusReady);
  const [idea, setIdea] = useState("");
  const [kitsTick, setKitsTick] = useState(0);

  async function handleStart(nextIdea: string) {
    setStatus(copy.statusThinking);
    await apiClient.createSession(nextIdea);
    setIdea(nextIdea);
    setStatus(copy.statusReady);
    setView("studio");
  }

  async function handleSaveKit() {
    const session = apiClient.getSession();
    const name = session?.projectName || "My kit";
    setStatus(copy.statusThinking);
    await apiClient.saveKit(name);
    setKitsTick((t) => t + 1);
    setStatus(copy.statusReady);
    setView("kits");
  }

  return (
    <AppShell view={view} status={status} onNavigate={setView}>
      {view === "home" && <HomeView onStart={handleStart} />}
      {view === "studio" && (
        <StudioView
          idea={idea || apiClient.getSession()?.idea || ""}
          onBuilt={() => setView("check")}
          setStatus={setStatus}
        />
      )}
      {view === "check" && (
        <CheckView onImprove={() => setView("improve")} onSave={handleSaveKit} />
      )}
      {view === "improve" && <ImproveView />}
      {view === "kits" && (
        <KitsView key={kitsTick} onOpenStudio={() => setView("studio")} />
      )}
      {view === "connections" && (
        <ConnectionsView setStatus={setStatus} />
      )}
      {view === "settings" && <SettingsView />}
    </AppShell>
  );
}
