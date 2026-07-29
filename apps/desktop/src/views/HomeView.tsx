import { useState } from "react";
import { copy } from "../copy/en";
import { VapButton } from "../components/ui/VapButton";
import { VapTextarea } from "../components/ui/VapInput";

type Props = {
  onStart: (idea: string) => void;
};

export function HomeView({ onStart }: Props) {
  const [idea, setIdea] = useState("");

  return (
    <section className="mx-auto flex min-h-[70vh] max-w-3xl flex-col justify-center">
      <p className="font-display text-5xl font-bold tracking-tight md:text-6xl">
        <span className="bg-gradient-to-r from-[var(--vap-peach)] via-[var(--vap-magenta)] to-[var(--vap-cyan)] bg-clip-text text-transparent glass-shimmer">
          {copy.brand}
        </span>
      </p>
      <h1 className="font-display mt-4 text-2xl font-semibold text-[var(--vap-ink)] md:text-3xl">
        {copy.tagline}
      </h1>
      <p className="mt-3 max-w-xl text-[var(--vap-muted)]">{copy.home.support}</p>

      <div className="mt-10 space-y-4">
        <VapTextarea
          value={idea}
          onChange={(e) => setIdea(e.target.value)}
          placeholder={copy.home.placeholder}
        />
        <div className="flex flex-wrap gap-2">
          {copy.home.examples.map((ex) => (
            <button
              key={ex}
              type="button"
              onClick={() => setIdea(ex)}
              className="rounded-full border border-[var(--glass-border)] bg-black/20 px-3 py-1 text-xs text-[var(--vap-muted)] hover:border-[var(--vap-cyan)] hover:text-[var(--vap-cyan)]"
            >
              {ex}
            </button>
          ))}
        </div>
        <VapButton
          variant="cyan"
          disabled={!idea.trim()}
          onClick={() => onStart(idea.trim())}
        >
          {copy.home.cta}
        </VapButton>
      </div>
    </section>
  );
}
