import { useEffect, useRef, useState } from "react";
import { api, Scenario, SessionDetail } from "../api/client";
import EvidencePanel from "../components/EvidencePanel";

export default function Metasploit() {
  const [scenario, setScenario] = useState<Scenario | null>(null);
  const [name, setName] = useState("Metasploit lab run");
  const [session, setSession] = useState<SessionDetail | null>(null);
  const [status, setStatus] = useState<"idle" | "starting" | "running" | "done" | "error">("idle");
  const [errorMsg, setErrorMsg] = useState("");
  const pollRef = useRef<number | null>(null);

  useEffect(() => {
    api.scenarios().then((s) => {
      const found = s.find((x) => x.module === "metasploit") || null;
      setScenario(found);
    });
  }, []);

  useEffect(() => () => { if (pollRef.current) window.clearInterval(pollRef.current); }, []);

  const start = async () => {
    if (!scenario) return;
    setStatus("starting");
    setErrorMsg("");
    try {
      const created = await api.createMetasploitSession({ name, scenario_id: scenario.id });
      setSession(created);
      setStatus("running");
      pollRef.current = window.setInterval(async () => {
        const updated = await api.getSession(created.id);
        setSession(updated);
        if (["succeeded", "failed", "cancelled", "timed_out"].includes(updated.status)) {
          setStatus("done");
          if (pollRef.current) window.clearInterval(pollRef.current);
        }
      }, 800);
    } catch (e) {
      setErrorMsg(String(e));
      setStatus("error");
    }
  };

  const cancel = async () => { if (session) await api.cancelSession(session.id); };

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-6">
      <h1 className="text-2xl font-semibold text-navy">Metasploit Experiment Workspace</h1>
      <p className="text-sm text-slateblue/70">
        Runs exactly one predefined, reviewed scenario against the single lab target configured in <code>backend/.env</code>
        (<code>LAB_TARGET_HOST</code>). The app refuses to run if that target isn't inside the configured isolated lab network.
        There is no exploit picker and no interactive shell in this UI.
      </p>

      {scenario && (
        <div className="bg-white border border-slateblue/10 rounded-md p-5 space-y-4">
          <div>
            <div className="font-semibold text-sm">{scenario.title}</div>
            <p className="text-xs text-slateblue/60 mt-1">{scenario.objective}</p>
            <p className="text-xs text-slateblue/60 mt-2">{scenario.description}</p>
          </div>
          <div>
            <label className="text-sm font-medium block mb-1">Session name</label>
            <input value={name} onChange={(e) => setName(e.target.value)} className="w-full border border-slateblue/20 rounded-md px-3 py-2 text-sm focus-ring" />
          </div>
          {errorMsg && <div className="text-sm text-red-700">{errorMsg}</div>}
          <div className="flex gap-3">
            <button onClick={start} disabled={status === "running" || status === "starting"} className="bg-teal text-white text-sm px-4 py-2 rounded-md disabled:opacity-40 focus-ring">
              {status === "starting" ? "Starting..." : "Run experiment"}
            </button>
            {status === "running" && <button onClick={cancel} className="text-sm px-4 py-2 rounded-md border border-slateblue/20 focus-ring">Cancel</button>}
          </div>
        </div>
      )}

      {session && <EvidencePanel session={session} />}
    </div>
  );
}
