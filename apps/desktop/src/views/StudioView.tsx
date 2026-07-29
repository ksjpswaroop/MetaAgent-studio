import { useEffect, useState } from "react";
import { copy } from "../copy/en";
import {
  apiClient,
  type DiscoveryQuestion,
  type PlanPath,
  type RoleRow,
} from "../lib/apiClient";
import { appState } from "../lib/appState";
import { logger } from "../lib/logger";
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
  const saved = appState.get().studio;
  const [step, setStep] = useState(saved.step);
  const [draft, setDraft] = useState(idea);
  const [questions, setQuestions] = useState<DiscoveryQuestion[]>([]);
  const [answers, setAnswers] = useState<string[]>(saved.answers);
  const [answer, setAnswer] = useState("");
  const [qIndex, setQIndex] = useState(saved.qIndex);
  const [paths, setPaths] = useState<PlanPath[]>([]);
  const [activePath, setActivePath] = useState<string>(saved.activePath);
  const [roles, setRoles] = useState<RoleRow[]>([]);
  const [building, setBuilding] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    setDraft(idea);
  }, [idea]);

  useEffect(() => {
    appState.patchStudio({
      step,
      answers,
      qIndex,
      activePath: activePath as "happy" | "ambiguity" | "failure",
    });
  }, [step, answers, qIndex, activePath]);

  useEffect(() => {
    if (step === 1 && !questions.length) {
      setStatus(copy.statusThinking);
      setError("");
      apiClient
        .startDiscovery()
        .then((qs) => {
          setQuestions(qs);
          setStatus(copy.statusReady);
        })
        .catch((e) => {
          setError(String(e));
          setStatus(copy.statusReady);
          logger.error("studio", "Discovery failed", { error: String(e) });
        });
    }
    if (step === 2 && !paths.length) {
      setStatus(copy.statusThinking);
      setError("");
      apiClient
        .planPaths()
        .then((p) => {
          setPaths(p);
          if (p[0]) setActivePath(p[0].kind);
          setStatus(copy.statusReady);
        })
        .catch((e) => {
          setError(String(e));
          setStatus(copy.statusReady);
        });
    }
    if (step === 3 && !roles.length) {
      setStatus(copy.statusThinking);
      setError("");
      apiClient
        .roles()
        .then((r) => {
          setRoles(r);
          setStatus(copy.statusReady);
        })
        .catch((e) => {
          setError(String(e));
          setStatus(copy.statusReady);
        });
    }
  }, [step, questions.length, paths.length, roles.length, setStatus]);

  function goStep(next: number) {
    setStep(next);
    setError("");
    logger.info("studio", `Wizard step ${next + 1}`, {
      label: copy.studio.steps[next],
    });
  }

  async function finishBuild() {
    setBuilding(true);
    setStatus(copy.statusThinking);
    setError("");
    try {
      await apiClient.buildKit();
      setStatus(copy.statusReady);
      onBuilt();
    } catch (e) {
      setError(String(e));
      setStatus(copy.statusReady);
    } finally {
      setBuilding(false);
    }
  }

  const active = paths.find((p) => p.kind === activePath) || paths[0];

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <StepDots steps={copy.studio.steps} current={step} />
      {error && (
        <GlassPanel className="border-[color:var(--li-warn)] p-4 text-sm text-[var(--li-warn)]">
          {error.includes("providers") || error.includes("Ollama") || error.includes("503")
            ? "Brain is offline or busy. Start Ollama and try again."
            : error}
        </GlassPanel>
      )}

      {step === 0 && (
        <GlassPanel className="space-y-4 p-6">
          <h2 className="font-display text-xl font-semibold">{copy.studio.steps[0]}</h2>
          <p className="text-sm text-[var(--vap-muted)]">{draft}</p>
          <VapButton onClick={() => goStep(1)}>{copy.studio.next}</VapButton>
        </GlassPanel>
      )}

      {step === 1 && (
        <GlassPanel className="space-y-4 p-6">
          <h2 className="font-display text-xl font-semibold">{copy.studio.steps[1]}</h2>
          <div className="space-y-3">
            {questions.slice(0, qIndex + 1).map((q, i) => (
              <div key={q.questionKey} className="space-y-2">
                <PlainChatBubble role="assistant">{q.content}</PlainChatBubble>
                {answers[i] && (
                  <PlainChatBubble role="user">{answers[i]}</PlainChatBubble>
                )}
              </div>
            ))}
          </div>
          {questions.length > 0 && qIndex < questions.length && (
            <div className="flex gap-2">
              <VapInput
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                placeholder="Type a short answer…"
              />
              <VapButton
                variant="cyan"
                disabled={!answer.trim()}
                onClick={async () => {
                  const q = questions[qIndex];
                  const text = answer.trim();
                  setStatus(copy.statusThinking);
                  try {
                    await apiClient.answerDiscovery(q.questionKey, text);
                    const next = [...answers, text];
                    setAnswers(next);
                    setAnswer("");
                    if (qIndex + 1 >= questions.length) {
                      setStatus("Finalizing…");
                      await apiClient.finalizeDiscovery();
                      goStep(2);
                    } else {
                      setQIndex(qIndex + 1);
                    }
                    setStatus(copy.statusReady);
                  } catch (e) {
                    setError(String(e));
                    setStatus(copy.statusReady);
                  }
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
                onClick={() => setActivePath(p.kind)}
                className={`rounded-full px-3 py-1 text-xs ${
                  activePath === p.kind
                    ? "bg-[var(--li-blue)] text-white"
                    : "border border-[var(--li-border)] bg-white/70 text-[var(--vap-muted)]"
                }`}
              >
                {p.title}
              </button>
            ))}
          </div>
          <p className="text-sm text-[var(--vap-muted)]">{active?.summary}</p>
          <pre className="overflow-x-auto rounded-xl border border-[var(--li-border)] bg-[var(--li-surface)] p-4 font-mono text-xs text-[var(--li-blue-dark)]">
            {active?.asciiFlow || ""}
          </pre>
          <div className="flex gap-2">
            <VapButton variant="ghost" onClick={() => goStep(1)}>
              {copy.studio.back}
            </VapButton>
            <VapButton
              disabled={!paths.length}
              onClick={async () => {
                setStatus(copy.statusThinking);
                try {
                  await apiClient.approvePlan();
                  goStep(3);
                  setStatus(copy.statusReady);
                } catch (e) {
                  setError(String(e));
                  setStatus(copy.statusReady);
                }
              }}
            >
              {copy.studio.approve}
            </VapButton>
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
                  <span className="text-xs font-medium text-[var(--li-blue)]">
                    {r.tierLabel}
                  </span>
                </div>
                <p className="mt-1 text-sm text-[var(--vap-muted)]">{r.blurb}</p>
              </li>
            ))}
          </ul>
          <div className="flex gap-2">
            <VapButton variant="ghost" onClick={() => goStep(2)}>
              {copy.studio.back}
            </VapButton>
            <VapButton disabled={!roles.length} onClick={() => goStep(4)}>
              {copy.studio.next}
            </VapButton>
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
