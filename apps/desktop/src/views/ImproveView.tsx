import { useEffect, useState } from "react";
import { copy } from "../copy/en";
import { apiClient, EdgeItem, PromptItem } from "../lib/apiClient";
import { GlassPanel } from "../components/ui/GlassPanel";
import { VapButton } from "../components/ui/VapButton";

export function ImproveView() {
  const [edges, setEdges] = useState<EdgeItem[]>([]);
  const [prompts, setPrompts] = useState<PromptItem[]>([]);
  const [copied, setCopied] = useState<string | null>(null);

  useEffect(() => {
    apiClient.edgeCases().then(setEdges);
    apiClient.codingPrompts().then(setPrompts);
  }, []);

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <h2 className="font-display text-2xl font-semibold">{copy.improve.title}</h2>

      <GlassPanel className="space-y-3 p-6">
        <h3 className="font-display text-lg font-semibold">{copy.improve.edges}</h3>
        <ul className="space-y-3">
          {edges.map((e) => (
            <li key={e.id} className="rounded-xl border border-[var(--glass-border)] bg-black/20 px-4 py-3">
              <p className="font-medium">{e.title}</p>
              <p className="mt-1 text-sm text-[var(--vap-muted)]">{e.detail}</p>
            </li>
          ))}
        </ul>
      </GlassPanel>

      <GlassPanel className="space-y-3 p-6">
        <h3 className="font-display text-lg font-semibold">{copy.improve.prompts}</h3>
        {prompts.map((p) => (
          <div key={p.id} className="rounded-xl border border-[var(--glass-border)] bg-black/20 p-4">
            <p className="font-medium">{p.title}</p>
            <pre className="mt-2 whitespace-pre-wrap font-mono text-xs text-[var(--vap-cyan)]">
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
        <VapButton variant="cyan">{copy.improve.iterate}</VapButton>
      </GlassPanel>
    </div>
  );
}
