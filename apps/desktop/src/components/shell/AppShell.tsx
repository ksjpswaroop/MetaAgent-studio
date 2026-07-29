import type { ReactNode } from "react";
import { copy, type ViewId } from "../../copy/en";

const NAV: { id: ViewId; label: string }[] = [
  { id: "home", label: copy.nav.home },
  { id: "studio", label: copy.nav.studio },
  { id: "check", label: copy.nav.check },
  { id: "improve", label: copy.nav.improve },
  { id: "kits", label: copy.nav.kits },
  { id: "settings", label: copy.nav.settings },
];

type Props = {
  view: ViewId;
  status: string;
  onNavigate: (v: ViewId) => void;
  children: ReactNode;
};

export function AppShell({ view, status, onNavigate, children }: Props) {
  return (
    <div className="flex min-h-screen">
      <aside className="flex w-[220px] shrink-0 flex-col border-r border-[var(--glass-border)] bg-black/25 px-4 py-6 backdrop-blur-xl">
        <div className="mb-8 px-2">
          <p className="font-display text-lg font-bold tracking-tight text-[var(--vap-ink)]">
            {copy.brand}
          </p>
          <p className="mt-1 text-[11px] uppercase tracking-[0.18em] text-[var(--vap-cyan)]">
            vapor studio
          </p>
        </div>
        <nav className="flex flex-1 flex-col gap-1">
          {NAV.map((item) => {
            const active = item.id === view;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => onNavigate(item.id)}
                className={`rounded-[var(--radius-control)] px-3 py-2.5 text-left text-sm transition ${
                  active
                    ? "border border-[var(--glass-border)] bg-[var(--glass-bg-strong)] text-[var(--vap-ink)]"
                    : "text-[var(--vap-muted)] hover:bg-[var(--glass-bg)] hover:text-[var(--vap-ink)]"
                }`}
              >
                {item.label}
              </button>
            );
          })}
        </nav>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-end border-b border-[var(--glass-border)] bg-black/20 px-6 py-3 backdrop-blur-md">
          <div className="rounded-full border border-[var(--vap-cyan)]/40 bg-[var(--vap-cyan)]/10 px-3 py-1 text-xs text-[var(--vap-cyan)]">
            {status}
          </div>
        </header>
        <main className="view-enter flex-1 overflow-auto p-6 md:p-10">{children}</main>
      </div>
    </div>
  );
}
