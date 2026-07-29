import { InputHTMLAttributes, TextareaHTMLAttributes } from "react";

const fieldClass =
  "w-full rounded-[var(--radius-control)] border border-[var(--glass-border)] bg-black/25 px-4 py-3 text-sm text-[var(--vap-ink)] placeholder:text-[var(--vap-muted)] outline-none focus:border-[var(--vap-cyan)]";

export function VapInput(props: InputHTMLAttributes<HTMLInputElement>) {
  const { className = "", ...rest } = props;
  return <input className={`${fieldClass} ${className}`} {...rest} />;
}

export function VapTextarea(props: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  const { className = "", ...rest } = props;
  return <textarea className={`${fieldClass} min-h-[140px] resize-y ${className}`} {...rest} />;
}
