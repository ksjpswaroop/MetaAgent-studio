import { useState } from "react";
import { copy } from "../copy/en";
import { apiClient, KitItem } from "../lib/apiClient";
import { GlassPanel } from "../components/ui/GlassPanel";
import { VapButton } from "../components/ui/VapButton";

type Props = { onOpenStudio: () => void };

export function KitsView({ onOpenStudio }: Props) {
  const [kits, setKits] = useState<KitItem[]>(() => apiClient.listKits());

  if (!kits.length) {
    return (
      <GlassPanel className="mx-auto max-w-xl p-8 text-center">
        <h2 className="font-display text-xl font-semibold">{copy.kits.title}</h2>
        <p className="mt-3 text-sm text-[var(--vap-muted)]">{copy.kits.empty}</p>
        <VapButton className="mt-6" variant="cyan" onClick={onOpenStudio}>
          {copy.nav.home}
        </VapButton>
      </GlassPanel>
    );
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <h2 className="font-display text-2xl font-semibold">{copy.kits.title}</h2>
      <div className="grid gap-4 sm:grid-cols-2">
        {kits.map((k) => (
          <GlassPanel key={k.id} className="space-y-3 p-5" strong>
            <p className="font-display text-lg font-semibold">{k.name}</p>
            <p className="text-sm text-[var(--vap-muted)]">
              Score {Math.round(k.score * 100)}
            </p>
            <div className="flex gap-2">
              <VapButton variant="ghost" onClick={onOpenStudio}>
                {copy.kits.open}
              </VapButton>
              <VapButton
                variant="cyan"
                onClick={() => {
                  const forked = {
                    ...k,
                    id: `${k.id}_fork`,
                    name: `${k.name} copy`,
                  };
                  const next = [forked, ...kits];
                  localStorage.setItem("mas_kits", JSON.stringify(next));
                  setKits(next);
                }}
              >
                {copy.kits.fork}
              </VapButton>
            </div>
          </GlassPanel>
        ))}
      </div>
    </div>
  );
}
