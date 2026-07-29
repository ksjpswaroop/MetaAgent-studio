import type { CSSProperties, ReactNode } from "react";

type Props = {
  children: ReactNode;
  className?: string;
  strong?: boolean;
  style?: CSSProperties;
};

export function GlassPanel({
  children,
  className = "",
  strong = false,
  style,
}: Props) {
  return (
    <div
      className={`rounded-[var(--radius-panel)] border border-[var(--glass-border)] shadow-[var(--shadow-chrome)] backdrop-blur-[var(--glass-blur)] ${
        strong ? "bg-[var(--glass-bg-strong)]" : "bg-[var(--glass-bg)]"
      } ${className}`}
      style={style}
    >
      {children}
    </div>
  );
}
