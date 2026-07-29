import type { InputHTMLAttributes, TextareaHTMLAttributes } from "react";

const fieldClass =
  "w-full rounded-[var(--radius-control)] border border-[var(--li-border)] bg-white/90 px-4 py-3 text-sm text-[var(--vap-ink)] placeholder:text-[var(--vap-muted)] outline-none focus:border-[var(--li-blue)] focus:ring-2 focus:ring-[var(--li-blue)]/15";

export function VapInput(props: InputHTMLAttributes<HTMLInputElement>) {
  const { className = "", ...rest } = props;
  return <input className={`${fieldClass} ${className}`} {...rest} />;
}

export function VapTextarea(props: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  const { className = "", ...rest } = props;
  return (
    <textarea className={`${fieldClass} min-h-[140px] resize-y ${className}`} {...rest} />
  );
}
