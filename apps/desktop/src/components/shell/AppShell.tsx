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
      <aside className="flex w-[220px] shrink-0 flex-col border-r border-[var(--glass-border)] bg-white/75 px-4 py-6 backdrop-blur-xl">
        <div className="mb-8 px-2">
          <p className="font-display text-lg font-bold tracking-tight text-[var(--li-blue)]">
            {copy.brand}
          </p>
          <p className="mt-1 text-[11px] uppercase tracking-[0.18em] text-[var(--li-muted)]">
            agent studio
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
                    ? "border border-[var(--glass-border)] bg-[var(--li-blue)] text-white"
                    : "text-[var(--vap-muted)] hover:bg-[var(--glass-bg)] hover:text-[var(--li-blue)]"
                }`}
              >
                {item.label}
              </button>
            );
          })}
        </nav>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-end border-b border-[var(--glass-border)] bg-white/60 px-6 py-3 backdrop-blur-md">
          <div className="rounded-full border border-[var(--li-blue)]/25 bg-[var(--li-blue)]/8 px-3 py-1 text-xs font-medium text-[var(--li-blue)]">
            {status}
          </div>
        </header>
        <main className="view-enter flex-1 overflow-auto p-6 md:p-10">{children}</main>
      </div>
    </div>
  );
}
