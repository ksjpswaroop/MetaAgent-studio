import { useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import { copy } from "../copy/en";
import { apiClient } from "../lib/apiClient";
import { GlassPanel } from "../components/ui/GlassPanel";
import { VapButton } from "../components/ui/VapButton";
import { VapInput } from "../components/ui/VapInput";

export function SettingsView() {
  const [key, setKey] = useState("");
  const [licenseMsg, setLicenseMsg] = useState("");
  const [brain, setBrain] = useState<"local" | "cloud">("local");
  const [exportPath, setExportPath] = useState("~/MetaAgentExports");
  const [devOpen, setDevOpen] = useState(false);
  const [greetMsg, setGreetMsg] = useState("");

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <h2 className="font-display text-2xl font-semibold">{copy.settings.title}</h2>

      <GlassPanel className="space-y-3 p-6">
        <label className="text-sm text-[var(--vap-muted)]">{copy.settings.license}</label>
        <VapInput
          value={key}
          onChange={(e) => setKey(e.target.value)}
          placeholder="MAS-PRO-XXXX-XXXX-XXXX"
        />
        <VapButton
          onClick={async () => {
            const res = await apiClient.activateLicense(key);
            setLicenseMsg(res.message);
          }}
        >
          {copy.settings.activate}
        </VapButton>
        {licenseMsg && <p className="text-xs text-[var(--vap-cyan)]">{licenseMsg}</p>}
      </GlassPanel>

      <GlassPanel className="space-y-3 p-6">
        <p className="text-sm text-[var(--vap-muted)]">{copy.settings.brain}</p>
        <div className="flex gap-2">
          {(["local", "cloud"] as const).map((b) => (
            <button
              key={b}
              type="button"
              onClick={() => setBrain(b)}
              className={`rounded-full px-4 py-1.5 text-sm ${
                brain === b
                  ? "bg-[var(--vap-magenta)] text-white"
                  : "border border-[var(--glass-border)] text-[var(--vap-muted)]"
              }`}
            >
              {b === "local" ? copy.settings.local : copy.settings.cloud}
            </button>
          ))}
        </div>
        <label className="mt-2 block text-sm text-[var(--vap-muted)]">
          {copy.settings.export}
        </label>
        <VapInput value={exportPath} onChange={(e) => setExportPath(e.target.value)} />
        <p className="text-xs text-[var(--vap-muted)]">API mode: {apiClient.mode()}</p>
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
                } catch (err) {
                  setGreetMsg(String(err));
                }
              }}
            >
              {copy.settings.greet}
            </VapButton>
            {greetMsg && (
              <p className="text-xs text-[var(--vap-cyan)]">{greetMsg}</p>
            )}
          </div>
        )}
      </GlassPanel>
    </div>
  );
}
