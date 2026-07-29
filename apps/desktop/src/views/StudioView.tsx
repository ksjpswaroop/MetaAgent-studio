import { useEffect, useState } from "react";
import { copy } from "../copy/en";
import { apiClient, PlanPath, RoleRow } from "../lib/apiClient";
import { GlassPanel } from "../components/ui/GlassPanel";
import { PlainChatBubble } from "../components/ui/PlainChatBubble";
import { StepDots } from "../components/ui/StepDots";
import { VapButton } from "../components/ui/VapButton";
import { VapInput } from "../components/ui/VapInput";

type Props = {
  idea: string;
  onBuilt: () => void;
  setStatus: (s: string) => void;
};

export function StudioView({ idea, onBuilt, setStatus }: Props) {
  const [step, setStep] = useState(0);
  const [draft, setDraft] = useState(idea);
  const [questions, setQuestions] = useState<string[]>([]);
  const [answers, setAnswers] = useState<string[]>([]);
  const [answer, setAnswer] = useState("");
  const [qIndex, setQIndex] = useState(0);
  const [paths, setPaths] = useState<PlanPath[]>([]);
  const [activePath, setActivePath] = useState<PlanPath["id"]>("happy");
  const [roles, setRoles] = useState<RoleRow[]>([]);
  const [building, setBuilding] = useState(false);

  useEffect(() => {
    setDraft(idea);
  }, [idea]);

  useEffect(() => {
    if (step === 1 && !questions.length) {
      setStatus(copy.statusThinking);
      apiClient.discoveryQuestions().then((qs) => {
        setQuestions(qs);
        setStatus(copy.statusReady);
      });
    }
    if (step === 2 && !paths.length) {
      apiClient.planPaths().then(setPaths);
    }
    if (step === 3 && !roles.length) {
      apiClient.roles().then(setRoles);
    }
  }, [step, questions.length, paths.length, roles.length, setStatus]);

  const pathCopy =
    activePath === "happy"
      ? copy.pathsAscii.happy
      : activePath === "ambiguity"
        ? copy.pathsAscii.ambiguity
        : copy.pathsAscii.failure;

  async function finishBuild() {
    setBuilding(true);
    setStatus(copy.statusThinking);
    await apiClient.buildKit();
    setStatus(copy.statusReady);
    setBuilding(false);
    onBuilt();
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <StepDots steps={copy.studio.steps} current={step} />

      {step === 0 && (
        <GlassPanel className="space-y-4 p-6">
          <h2 className="font-display text-xl font-semibold">{copy.studio.steps[0]}</h2>
          <p className="text-sm text-[var(--vap-muted)]">{draft}</p>
          <VapButton onClick={() => setStep(1)}>{copy.studio.next}</VapButton>
        </GlassPanel>
      )}

      {step === 1 && (
        <GlassPanel className="space-y-4 p-6">
          <h2 className="font-display text-xl font-semibold">{copy.studio.steps[1]}</h2>
          <div className="space-y-3">
            {questions.slice(0, qIndex + 1).map((q, i) => (
              <div key={q} className="space-y-2">
                <PlainChatBubble role="assistant">{q}</PlainChatBubble>
                {answers[i] && <PlainChatBubble role="user">{answers[i]}</PlainChatBubble>}
              </div>
            ))}
          </div>
          {qIndex < questions.length && (
            <div className="flex gap-2">
              <VapInput
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                placeholder="Type a short answer…"
              />
              <VapButton
                variant="cyan"
                disabled={!answer.trim()}
                onClick={() => {
                  const next = [...answers, answer.trim()];
                  setAnswers(next);
                  setAnswer("");
                  if (qIndex + 1 >= questions.length) setStep(2);
                  else setQIndex(qIndex + 1);
                }}
              >
                {copy.studio.next}
              </VapButton>
            </div>
          )}
        </GlassPanel>
      )}

      {step === 2 && (
        <GlassPanel className="space-y-4 p-6">
          <h2 className="font-display text-xl font-semibold">{copy.studio.steps[2]}</h2>
          <div className="flex flex-wrap gap-2">
            {paths.map((p) => (
              <button
                key={p.id}
                type="button"
                onClick={() => setActivePath(p.id)}
                className={`rounded-full px-3 py-1 text-xs ${
                  activePath === p.id
                    ? "bg-[var(--li-blue)] text-white"
                    : "border border-[var(--li-border)] bg-white/70 text-[var(--vap-muted)]"
                }`}
              >
                {p.id === "happy"
                  ? copy.studio.paths.happy
                  : p.id === "ambiguity"
                    ? copy.studio.paths.ambiguity
                    : copy.studio.paths.failure}
              </button>
            ))}
          </div>
          <p className="text-sm text-[var(--vap-muted)]">
            {paths.find((p) => p.id === activePath)?.summary}
          </p>
          <pre className="overflow-x-auto rounded-xl border border-[var(--li-border)] bg-[var(--li-surface)] p-4 font-mono text-xs text-[var(--li-blue-dark)]">
            {pathCopy}
          </pre>
          <div className="flex gap-2">
            <VapButton variant="ghost" onClick={() => setStep(1)}>
              {copy.studio.back}
            </VapButton>
            <VapButton onClick={() => setStep(3)}>{copy.studio.approve}</VapButton>
          </div>
        </GlassPanel>
      )}

      {step === 3 && (
        <GlassPanel className="space-y-4 p-6">
          <h2 className="font-display text-xl font-semibold">{copy.studio.steps[3]}</h2>
          <ul className="space-y-3">
            {roles.map((r) => (
              <li
                key={r.name}
                className="rounded-xl border border-[var(--li-border)] bg-white/80 px-4 py-3"
              >
                <div className="flex items-center justify-between gap-3">
                  <p className="font-display font-semibold">{r.name}</p>
                  <span className="text-xs font-medium text-[var(--li-blue)]">{r.tierLabel}</span>
                </div>
                <p className="mt-1 text-sm text-[var(--vap-muted)]">{r.blurb}</p>
              </li>
            ))}
          </ul>
          <div className="flex gap-2">
            <VapButton variant="ghost" onClick={() => setStep(2)}>
              {copy.studio.back}
            </VapButton>
            <VapButton onClick={() => setStep(4)}>{copy.studio.next}</VapButton>
          </div>
        </GlassPanel>
      )}

      {step === 4 && (
        <GlassPanel className="space-y-4 p-6">
          <h2 className="font-display text-xl font-semibold">{copy.studio.steps[4]}</h2>
          <p className="text-sm text-[var(--vap-muted)]">
            We’ll package your helper and run a quick check. This may take a moment.
          </p>
          <VapButton variant="cyan" disabled={building} onClick={finishBuild}>
            {building ? copy.statusThinking : copy.studio.buildCta}
          </VapButton>
        </GlassPanel>
      )}
    </div>
  );
}
