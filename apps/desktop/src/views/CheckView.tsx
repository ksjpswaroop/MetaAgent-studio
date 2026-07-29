import { copy } from "../copy/en";
import { apiClient } from "../lib/apiClient";
import { GlassPanel } from "../components/ui/GlassPanel";
import { ScoreRing } from "../components/ui/ScoreRing";
import { VapButton } from "../components/ui/VapButton";

type Props = {
  onImprove: () => void;
  onSave: () => void;
};

export function CheckView({ onImprove, onSave }: Props) {
  const check = apiClient.getCheck();

  if (!check) {
    return (
      <GlassPanel className="mx-auto max-w-xl p-8 text-center">
        <h2 className="font-display text-xl font-semibold">{copy.check.title}</h2>
        <p className="mt-3 text-sm text-[var(--vap-muted)]">{copy.check.empty}</p>
      </GlassPanel>
    );
  }

  const rows = [
    { ok: check.packageOk, label: copy.check.packageOk },
    { ok: check.testsOk, label: copy.check.testsOk },
    { ok: check.zipOk, label: copy.check.zipOk },
  ];

  return (
    <div className="mx-auto grid max-w-3xl gap-6 md:grid-cols-[auto_1fr]">
      <GlassPanel className="flex items-center justify-center p-8">
        <ScoreRing value={check.overall} label={copy.check.score} />
      </GlassPanel>
      <GlassPanel className="space-y-4 p-6">
        <h2 className="font-display text-xl font-semibold">{copy.check.title}</h2>
        <ul className="space-y-2 text-sm">
          {rows.map((r) => (
            <li key={r.label} className="flex items-center gap-2">
              <span className={r.ok ? "text-[var(--vap-cyan)]" : "text-[var(--vap-peach)]"}>
                {r.ok ? "●" : "○"}
              </span>
              {r.label}
            </li>
          ))}
        </ul>
        <div className="flex flex-wrap gap-2 pt-2">
          <VapButton variant="ghost" onClick={onImprove}>
            {copy.check.improve}
          </VapButton>
          <VapButton variant="cyan" onClick={onSave}>
            {copy.check.save}
          </VapButton>
        </div>
      </GlassPanel>
    </div>
  );
}
