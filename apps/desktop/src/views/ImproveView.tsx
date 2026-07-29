import { useEffect, useState } from "react";
import { copy } from "../copy/en";
import { apiClient, type EdgeItem, type PromptItem } from "../lib/apiClient";
import { GlassPanel } from "../components/ui/GlassPanel";
import { VapButton } from "../components/ui/VapButton";

type Props = {
  setStatus: (s: string) => void;
};

export function ImproveView({ setStatus }: Props) {
  const [edges, setEdges] = useState<EdgeItem[]>([]);
  const [prompts, setPrompts] = useState<PromptItem[]>([]);
  const [copied, setCopied] = useState<string | null>(null);
  const [notes, setNotes] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function load() {
    setError("");
    try {
      const [e, p] = await Promise.all([
        apiClient.edgeCases(),
        apiClient.codingPrompts(),
      ]);
      setEdges(e);
      setPrompts(p);
    } catch (err) {
      setError(String(err));
    }
  }

  useEffect(() => {
    void load();
  }, []);

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <h2 className="font-display text-2xl font-semibold">{copy.improve.title}</h2>
      {error && (
        <p className="text-sm text-[var(--li-warn)]">{error}</p>
      )}
      {notes && (
        <p className="text-sm text-[var(--li-success)]">{notes}</p>
      )}

      <GlassPanel className="space-y-3 p-6">
        <h3 className="font-display text-lg font-semibold">{copy.improve.edges}</h3>
        <ul className="space-y-3">
          {edges.map((e) => (
            <li
              key={e.id}
              className="rounded-xl border border-[var(--li-border)] bg-white/80 px-4 py-3"
            >
              <p className="font-medium">{e.title}</p>
              <p className="mt-1 text-sm text-[var(--vap-muted)]">{e.detail}</p>
            </li>
          ))}
        </ul>
      </GlassPanel>

      <GlassPanel className="space-y-3 p-6">
        <h3 className="font-display text-lg font-semibold">{copy.improve.prompts}</h3>
        {prompts.map((p) => (
          <div
            key={p.id}
            className="rounded-xl border border-[var(--li-border)] bg-white/80 p-4"
          >
            <p className="font-medium">{p.title}</p>
            <pre className="mt-2 whitespace-pre-wrap font-mono text-xs text-[var(--li-blue-dark)]">
              {p.prompt}
            </pre>
            <VapButton
              className="mt-3"
              variant="ghost"
              onClick={async () => {
                await navigator.clipboard.writeText(p.prompt);
                setCopied(p.id);
              }}
            >
              {copied === p.id ? "Copied" : copy.improve.copyPrompt}
            </VapButton>
          </div>
        ))}
        <VapButton
          variant="cyan"
          disabled={busy}
          onClick={async () => {
            setBusy(true);
            setStatus(copy.statusThinking);
            try {
              const res = await apiClient.iterateImprove();
              setNotes(
                res.notes ||
                  `Improved${res.scoreAfter != null ? ` — score ${Math.round(res.scoreAfter * 100)}` : ""}`,
              );
              await load();
            } catch (err) {
              setError(String(err));
            } finally {
              setBusy(false);
              setStatus(copy.statusReady);
            }
          }}
        >
          {copy.improve.iterate}
        </VapButton>
      </GlassPanel>
    </div>
  );
}
