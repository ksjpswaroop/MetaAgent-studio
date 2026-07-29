type Props = { value: number; label: string };

export function ScoreRing({ value, label }: Props) {
  const pct = Math.round(value * 100);
  return (
    <div className="flex flex-col items-center gap-2">
      <div
        className="grid h-28 w-28 place-items-center rounded-full border-4 border-[var(--li-blue)]/25"
        style={{
          background: `conic-gradient(var(--li-blue) ${pct}%, rgba(10,102,194,0.08) 0)`,
        }}
      >
        <div className="grid h-20 w-20 place-items-center rounded-full bg-white font-display text-2xl font-bold text-[var(--li-blue)]">
          {pct}
        </div>
      </div>
      <p className="text-xs text-[var(--vap-muted)]">{label}</p>
    </div>
  );
}
