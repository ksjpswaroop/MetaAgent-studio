type Props = {
  role: "assistant" | "user";
  children: string;
};

export function PlainChatBubble({ role, children }: Props) {
  const mine = role === "user";
  return (
    <div className={`flex ${mine ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
          mine
            ? "bg-[var(--li-blue)] text-white"
            : "border border-[var(--li-border)] bg-white text-[var(--vap-ink)]"
        }`}
      >
        {children}
      </div>
    </div>
  );
}
