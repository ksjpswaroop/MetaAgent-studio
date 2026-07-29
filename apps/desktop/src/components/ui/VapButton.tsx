import type { ButtonHTMLAttributes, ReactNode } from "react";

type Variant = "primary" | "cyan" | "ghost" | "danger";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode;
  variant?: Variant;
};

const variants: Record<Variant, string> = {
  primary:
    "bg-[color:var(--li-blue)] text-white shadow-[0_4px_16px_rgba(10,102,194,0.28)] hover:bg-[color:var(--li-blue-dark)]",
  cyan:
    "bg-[color:var(--li-blue-soft)] text-white shadow-[0_4px_16px_rgba(55,143,233,0.25)] hover:bg-[color:var(--li-blue)]",
  ghost:
    "bg-white/80 text-[color:var(--li-ink)] border border-[color:var(--li-border)] hover:bg-white hover:border-[color:var(--li-blue-soft)]",
  danger: "bg-[#cc1016] text-white hover:brightness-110",
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
