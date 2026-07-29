import type { ButtonHTMLAttributes, ReactNode } from "react";

type Variant = "primary" | "cyan" | "ghost" | "danger";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode;
  variant?: Variant;
};

const variants: Record<Variant, string> = {
  primary:
    "bg-[color:var(--vap-magenta)] text-white shadow-[0_4px_20px_rgba(255,43,214,0.3)] hover:brightness-110",
  cyan:
    "bg-[color:var(--vap-cyan)] text-[color:var(--vap-night)] shadow-[0_4px_20px_rgba(45,226,230,0.28)] hover:brightness-105",
  ghost:
    "bg-white/10 text-[color:var(--vap-ink)] border border-white/30 hover:bg-white/20",
  danger: "bg-rose-600/90 text-white hover:brightness-110",
};

export function VapButton({
  children,
  variant = "primary",
  className = "",
  type = "button",
  ...rest
}: Props) {
  return (
    <button
      type={type}
      className={`inline-flex items-center justify-center gap-2 rounded-[var(--radius-control)] px-5 py-2.5 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-50 ${variants[variant]} ${className}`}
      {...rest}
    >
      {children}
    </button>
  );
}
