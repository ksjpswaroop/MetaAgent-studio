type Props = {
  steps: readonly string[];
  current: number;
};

export function StepDots({ steps, current }: Props) {
  return (
    <ol className="flex flex-wrap gap-2">
      {steps.map((label, i) => {
        const active = i === current;
        const done = i < current;
        return (
          <li
            key={label}
            className={`flex items-center gap-2 rounded-full border px-3 py-1 text-xs ${
              active
                ? "border-[var(--li-blue)] text-[var(--li-blue)] animate-[step-pulse_2s_ease-in-out_infinite]"
                : done
                  ? "border-[var(--li-success)]/40 text-[var(--li-success)]"
                  : "border-[var(--li-border)] text-[var(--vap-muted)]"
            }`}
          >
            <span className="font-display font-semibold">{i + 1}</span>
            <span>{label}</span>
          </li>
        );
      })}
    </ol>
  );
}
