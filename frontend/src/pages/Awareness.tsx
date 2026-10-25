import { useEffect, useState } from "react";
import { AlertTriangle, ShieldAlert, Globe2, LockKeyhole } from "lucide-react";
import { api, AwarenessScenario, SessionDetail } from "../api/client";

type Phase = "pick" | "narrative" | "portal" | "debrief";

export default function Awareness() {
  const [scenarios, setScenarios] = useState<AwarenessScenario[]>([]);
  const [chosen, setChosen] = useState<AwarenessScenario | null>(null);
  const [phase, setPhase] = useState<Phase>("pick");
  const [decisions, setDecisions] = useState<Record<string, string>>({});
  const [result, setResult] = useState<SessionDetail | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => { api.awarenessScenarios().then(setScenarios).catch((e) => setError(String(e))); }, []);

  const pick = (s: AwarenessScenario) => {
    setChosen(s);
    setDecisions({});
    setResult(null);
    setPhase("narrative");
  };

  const choose = async (stepId: string, option: string) => {
    if (submitting) return;
    const next = { ...decisions, [stepId]: option };
    setDecisions(next);
    if (!chosen) return;
    if (Object.keys(next).length >= chosen.steps.length) {
      try {
        setSubmitting(true);
        const session = await api.createAwarenessSession({ name: `Awareness: ${chosen.title}`, scenario_id: chosen.id });
        const submitted = await api.submitAwareness(session.id, next);
        setResult(submitted);
        setPhase("debrief");
      } catch (e) {
        setError(e instanceof Error ? e.message : "Could not submit the simulation");
      } finally {
        setSubmitting(false);
      }
    }
  };

  return (
    <div className="p-8 max-w-3xl mx-auto space-y-6">
      <h1 className="text-2xl font-semibold text-navy">Social-Engineering Awareness Simulator</h1>
      <p className="text-sm text-slateblue/70">
        A browser-only simulation with invented, fictional Wi-Fi branding. No real network is created, and no real or dummy
        credentials you type are ever stored -- only your decisions and a score.
      </p>
      {error && <div className="border border-red-200 bg-red-50 text-red-800 rounded-md p-3 text-sm">{error}</div>}

      {phase === "pick" && (
        <div className="grid gap-4">
          {scenarios.map((s) => (
            <button key={s.id} onClick={() => pick(s)} className="text-left bg-white border border-slateblue/10 rounded-md p-5 hover:border-teal focus-ring">
              <div className="font-semibold text-sm">{s.title}</div>
              <div className="text-xs text-slateblue/60 mt-1">{s.brand}</div>
            </button>
          ))}
        </div>
      )}

      {phase === "narrative" && chosen && (
        <div className="bg-white border border-slateblue/10 rounded-md p-6 space-y-4">
          <div className="text-xs uppercase tracking-wide text-teal font-semibold">Scenario</div>
          <p className="text-sm">{chosen.narrative}</p>
          <button onClick={() => setPhase("portal")} className="bg-teal text-white text-sm px-4 py-2 rounded-md focus-ring">Inspect the portal</button>
        </div>
      )}

      {phase === "portal" && chosen && (
        <div className="space-y-4">
          <div className="bg-slate-100 border border-slateblue/20 rounded-xl p-2 shadow-sm">
            <div className="bg-white rounded-lg overflow-hidden">
              <div className="flex items-center gap-2 px-3 py-2 border-b border-slateblue/10 text-xs text-slateblue/60">
                <Globe2 size={14} /> portal.cloudharbor.example <LockKeyhole size={13} className="ml-auto text-teal" />
              </div>
              <div className="p-5 bg-gradient-to-br from-iceblue to-white">
                <div className="text-xs uppercase tracking-widest text-teal font-semibold">{chosen.brand}</div>
                <div className="text-lg font-semibold text-navy mt-1">Connect to guest internet</div>
                <p className="text-xs text-slateblue/70 mt-1">Inspect the details before choosing how to continue.</p>
              </div>
            </div>
          </div>
          {chosen.steps.map((step) => (
            <div key={step.id} className="bg-white border border-slateblue/10 rounded-md p-6 space-y-3">
              <div className="flex items-center gap-2 text-sm font-medium">
                <ShieldAlert size={16} className="text-amber-500" /> {step.prompt}
              </div>
              <div className="grid gap-2">
                {step.options.map((opt) => (
                  <button
                    key={opt}
                    onClick={() => choose(step.id, opt)}
                    disabled={submitting}
                    className={`text-left text-sm border rounded-md px-3 py-2 hover:border-teal focus-ring ${
                      decisions[step.id] === opt
                        ? "border-teal bg-iceblue font-medium"
                        : "border-slateblue/20"
                    }`}
                  >
                    {opt}
                  </button>
                ))}
              </div>
              {decisions[step.id] && (
                <div className={`rounded-md border p-3 text-sm ${
                  decisions[step.id] === step.safe_option
                    ? "border-green-200 bg-green-50 text-green-900"
                    : "border-amber-200 bg-amber-50 text-amber-900"
                }`}>
                  <div className="font-semibold">
                    {decisions[step.id] === step.safe_option ? "Good decision" : "Think twice"}
                  </div>
                  <div className="mt-1">
                    You chose: <span className="font-medium">{decisions[step.id]}</span>
                  </div>
                  {decisions[step.id] !== step.safe_option && (
                    <div className="mt-1">
                      Safer choice: <span className="font-medium">{step.safe_option}</span>
                    </div>
                  )}
                  <div className="mt-1 text-xs">{step.red_flag}</div>
                </div>
              )}
            </div>
          ))}
          <p className="text-xs text-slateblue/50">If you choose to "proceed", any credential field in a real version of this simulator would only ever accept a fixed dummy value -- never free text.</p>
          {submitting && <p className="text-sm text-teal">Recording your decisions...</p>}
        </div>
      )}

      {phase === "debrief" && result && (
        <div className="bg-white border border-slateblue/10 rounded-md p-6 space-y-4">
          <div className="text-lg font-semibold text-navy">Awareness score: {String(result.input_summary.score)}/100</div>
          <div className="text-sm text-slateblue/70">
            {String(result.input_summary.red_flags_spotted)} of {String(result.input_summary.red_flags_total)} red flags spotted.
          </div>
          <div className="space-y-3">
            {(result.evidence.debrief as Array<{ prompt: string; red_flag: string; chosen: string; was_safe_choice: boolean; safe_option: string }>).map((d, i) => (
              <div key={i} className={`border rounded-md p-3 text-sm ${d.was_safe_choice ? "border-green-200 bg-green-50" : "border-amber-200 bg-amber-50"}`}>
                <div className="flex items-center gap-2 font-medium">
                  {!d.was_safe_choice && <AlertTriangle size={14} className="text-amber-600" />} {d.prompt}
                </div>
                <div className="text-xs mt-1">You chose: <span className="font-medium">{d.chosen}</span></div>
                {!d.was_safe_choice && <div className="text-xs mt-1">Safer choice: <span className="font-medium">{d.safe_option}</span></div>}
                <div className="text-xs mt-1 text-slateblue/70">Why it matters: {d.red_flag}</div>
              </div>
            ))}
          </div>
          <button onClick={() => setPhase("pick")} className="text-sm text-teal underline">Try another scenario</button>
        </div>
      )}
    </div>
  );
}
