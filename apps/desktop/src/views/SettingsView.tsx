import { useEffect, useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import { copy } from "../copy/en";
import { useActivityLog } from "../hooks/useActivityLog";
import { useAppState } from "../hooks/useAppState";
import { apiClient } from "../lib/apiClient";
import { appState } from "../lib/appState";
import { logger } from "../lib/logger";
import { GlassPanel } from "../components/ui/GlassPanel";
import { VapButton } from "../components/ui/VapButton";
import { VapInput } from "../components/ui/VapInput";

function levelColor(level: string): string {
  if (level === "error") return "text-[#cc1016]";
  if (level === "warn") return "text-[var(--li-warn)]";
  if (level === "debug") return "text-[var(--vap-muted)]";
  return "text-[var(--li-blue)]";
}

export function SettingsView() {
  const ui = useAppState();
  const logs = useActivityLog();
  const [demoUnlocked, setDemoUnlocked] = useState(false);
  const [licenseMsg, setLicenseMsg] = useState("");
  const [brainMsg, setBrainMsg] = useState("");
  const [devOpen, setDevOpen] = useState(false);
  const [greetMsg, setGreetMsg] = useState("");
  const [providerId, setProviderId] = useState("prov_ollama");

  useEffect(() => {
    apiClient
      .health()
      .then((h) => setDemoUnlocked(h.demoUnlock))
      .catch(() => undefined);
    apiClient
      .licenseStatus()
      .then((s) => {
        if (s.features?.includes("demo_unlock")) setDemoUnlocked(true);
      })
      .catch(() => undefined);
    apiClient
      .listProviders()
      .then((ps) => {
        const ollama = ps.find((p) => p.name === "ollama");
        if (ollama) setProviderId(ollama.id);
      })
      .catch(() => undefined);
    apiClient
      .getSettings()
      .then((s) => {
        if (typeof s.export_path === "string") {
          appState.patchSettings({ exportPath: s.export_path as string });
        }
      })
      .catch(() => undefined);
  }, []);

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <h2 className="font-display text-2xl font-semibold">{copy.settings.title}</h2>

      {demoUnlocked ? (
        <GlassPanel className="space-y-2 p-6">
          <p className="font-display font-semibold text-[var(--li-blue)]">
            Investor demo — all features unlocked
          </p>
          <p className="text-sm text-[var(--vap-muted)]">
            No subscription key required for this build.
          </p>
        </GlassPanel>
      ) : (
        <GlassPanel className="space-y-3 p-6">
          <label className="text-sm text-[var(--vap-muted)]">{copy.settings.license}</label>
          <VapInput
            value={ui.settings.licenseKey}
            onChange={(e) => appState.patchSettings({ licenseKey: e.target.value })}
            placeholder="MAS-PRO-XXXX-XXXX-XXXX"
          />
          <VapButton
            onClick={async () => {
              const res = await apiClient.activateLicense(ui.settings.licenseKey);
              setLicenseMsg(res.message);
            }}
          >
            {copy.settings.activate}
          </VapButton>
          {licenseMsg && <p className="text-xs text-[var(--li-blue)]">{licenseMsg}</p>}
        </GlassPanel>
      )}

      <GlassPanel className="space-y-3 p-6">
        <p className="text-sm text-[var(--vap-muted)]">{copy.settings.brain}</p>
        <div className="flex gap-2">
          {(["local", "cloud"] as const).map((b) => (
            <button
              key={b}
              type="button"
              onClick={() => appState.patchSettings({ brain: b })}
              className={`rounded-full px-4 py-1.5 text-sm ${
                ui.settings.brain === b
                  ? "bg-[var(--li-blue)] text-white"
                  : "border border-[var(--li-border)] bg-white/80 text-[var(--vap-muted)]"
              }`}
            >
              {b === "local" ? copy.settings.local : copy.settings.cloud}
            </button>
          ))}
        </div>
        <VapButton
          variant="cyan"
          onClick={async () => {
            try {
              const res = await apiClient.testProvider(providerId);
              setBrainMsg(
                res.ok
                  ? `Brain OK${res.latency_ms != null ? ` (${res.latency_ms} ms)` : ""}`
                  : res.message || "Brain offline",
              );
              logger.info("settings", res.ok ? "Brain test ok" : "Brain test failed", {
                message: res.message,
              });
            } catch (e) {
              setBrainMsg(String(e));
            }
          }}
        >
          Test brain (Ollama)
        </VapButton>
        {brainMsg && <p className="text-xs text-[var(--li-blue)]">{brainMsg}</p>}
        <label className="mt-2 block text-sm text-[var(--vap-muted)]">
          {copy.settings.export}
        </label>
        <VapInput
          value={ui.settings.exportPath}
          onChange={(e) => appState.patchSettings({ exportPath: e.target.value })}
          onBlur={() => {
            void apiClient.putSettings({ export_path: ui.settings.exportPath });
          }}
        />
        <p className="text-xs text-[var(--vap-muted)]">API: {apiClient.baseUrl()}</p>
        {apiClient.getSession() && (
          <p className="text-xs text-[var(--vap-muted)]">
            Session: {apiClient.getSession()!.id} · {apiClient.getSession()!.stage}
          </p>
        )}
      </GlassPanel>

      <GlassPanel className="space-y-3 p-6">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h3 className="font-display text-lg font-semibold">
              {copy.settings.activity}
            </h3>
            <p className="text-xs text-[var(--vap-muted)]">
              {copy.settings.activitySupport}
            </p>
          </div>
          <VapButton
            variant="ghost"
            onClick={() => logger.clear()}
            disabled={!logs.length}
          >
            {copy.settings.activityClear}
          </VapButton>
        </div>
        {!logs.length ? (
          <p className="text-sm text-[var(--vap-muted)]">{copy.settings.activityEmpty}</p>
        ) : (
          <ul className="max-h-64 space-y-2 overflow-auto rounded-xl border border-[var(--li-border)] bg-[var(--li-surface)] p-3">
            {logs.slice(0, 50).map((entry) => (
              <li key={entry.id} className="text-xs leading-relaxed">
                <span className="text-[var(--vap-muted)]">
                  {new Date(entry.ts).toLocaleTimeString()}
                </span>{" "}
                <span className={`font-semibold uppercase ${levelColor(entry.level)}`}>
                  {entry.level}
                </span>{" "}
                <span className="text-[var(--li-blue-dark)]">{entry.source}</span>
                {" — "}
                <span>{entry.message}</span>
              </li>
            ))}
          </ul>
        )}
      </GlassPanel>

      <GlassPanel className="p-6">
        <button
          type="button"
          className="text-sm text-[var(--vap-muted)] underline-offset-2 hover:underline"
          onClick={() => setDevOpen((v) => !v)}
        >
          {copy.settings.developer}
        </button>
        {devOpen && (
          <div className="mt-4 space-y-3">
            <VapButton
              variant="ghost"
              onClick={async () => {
                try {
                  const msg = await invoke<string>("greet", { name: "Studio" });
                  setGreetMsg(msg);
                  logger.info("tauri", "Rust greet ok");
                } catch (err) {
                  setGreetMsg(String(err));
                  logger.error("tauri", "Rust greet failed", {
                    error: String(err),
                  });
                }
              }}
            >
              {copy.settings.greet}
            </VapButton>
            {greetMsg && (
              <p className="text-xs text-[var(--li-blue)]">{greetMsg}</p>
            )}
          </div>
        )}
      </GlassPanel>
    </div>
  );
}
