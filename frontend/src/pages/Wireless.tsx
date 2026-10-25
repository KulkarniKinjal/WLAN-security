import { useEffect, useRef, useState } from "react";
import { UploadCloud } from "lucide-react";
import { api, Scenario, SessionDetail, UploadResult, WordlistItem } from "../api/client";
import EvidencePanel from "../components/EvidencePanel";

export default function Wireless() {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [wordlists, setWordlists] = useState<WordlistItem[]>([]);
  const [scenarioId, setScenarioId] = useState("");
  const [upload, setUpload] = useState<UploadResult | null>(null);
  const [wordlistId, setWordlistId] = useState("");
  const [name, setName] = useState("Wireless experiment");
  const [session, setSession] = useState<SessionDetail | null>(null);
  const [status, setStatus] = useState<"idle" | "uploading" | "starting" | "running" | "done" | "error">("idle");
  const [errorMsg, setErrorMsg] = useState("");
  const pollRef = useRef<number | null>(null);

  useEffect(() => {
    api.scenarios().then((s) => {
      const wireless = s.filter((x) => x.module === "wireless_wep" || x.module === "wireless_wpa");
      setScenarios(wireless);
      if (wireless.length) setScenarioId(wireless[0].id);
    });
    api.wordlists().then(setWordlists);
  }, []);

  useEffect(() => () => { if (pollRef.current) window.clearInterval(pollRef.current); }, []);

  const selectedScenario = scenarios.find((s) => s.id === scenarioId);

  const onFile = async (file: File) => {
    setStatus("uploading");
    setErrorMsg("");
    try {
      const result = await api.uploadCapture(file);
      setUpload(result);
      setStatus("idle");
    } catch (e) {
      setErrorMsg(String(e));
      setStatus("error");
    }
  };

  const startExperiment = async () => {
    if (!upload || !selectedScenario) return;
    if (selectedScenario.requires_wordlist && !wordlistId) {
      setErrorMsg("Select a wordlist for this scenario.");
      return;
    }
    setStatus("starting");
    setErrorMsg("");
    try {
      const created = await api.createWirelessSession({
        name, scenario_id: selectedScenario.id, capture_upload_id: upload.upload_id,
        wordlist_id: selectedScenario.requires_wordlist ? wordlistId : undefined,
      });
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

  const cancel = async () => {
    if (!session) return;
    await api.cancelSession(session.id);
  };

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-6">
      <h1 className="text-2xl font-semibold text-navy">Wireless Experiment Workspace</h1>
      <p className="text-sm text-slateblue/70">
        Works only against authorized offline capture files you upload. No live wireless capture or injection happens here.
      </p>

      <div className="bg-white border border-slateblue/10 rounded-md p-5 space-y-4">
        <div>
          <label className="text-sm font-medium block mb-1">Session name</label>
          <input value={name} onChange={(e) => setName(e.target.value)} className="w-full border border-slateblue/20 rounded-md px-3 py-2 text-sm focus-ring" />
        </div>

        <div>
          <label className="text-sm font-medium block mb-1">Scenario</label>
          <select value={scenarioId} onChange={(e) => setScenarioId(e.target.value)} className="w-full border border-slateblue/20 rounded-md px-3 py-2 text-sm focus-ring">
            {scenarios.map((s) => <option key={s.id} value={s.id}>{s.title}</option>)}
          </select>
          {selectedScenario && <p className="text-xs text-slateblue/60 mt-2">{selectedScenario.description}</p>}
        </div>

        <div>
          <label className="text-sm font-medium block mb-1">Capture file (.pcap / .pcapng / .cap)</label>
          <label className="flex items-center gap-2 border-2 border-dashed border-slateblue/20 rounded-md px-3 py-6 text-sm text-slateblue/60 cursor-pointer hover:border-teal focus-ring">
            <UploadCloud size={18} />
            {upload ? `${upload.filename} (${upload.size_bytes} bytes)` : "Click to choose a file"}
            <input type="file" accept=".pcap,.pcapng,.cap" className="hidden" onChange={(e) => e.target.files && onFile(e.target.files[0])} />
          </label>
          {upload && (
            <p className="text-xs text-slateblue/60 mt-2">
              Metadata: {upload.metadata.available ? upload.metadata.raw : `unavailable (${upload.metadata.reason})`}
            </p>
          )}
        </div>

        {selectedScenario?.requires_wordlist && (
          <div>
            <label className="text-sm font-medium block mb-1">Wordlist</label>
            <select value={wordlistId} onChange={(e) => setWordlistId(e.target.value)} className="w-full border border-slateblue/20 rounded-md px-3 py-2 text-sm focus-ring">
              <option value="">Select a wordlist...</option>
              {wordlists.map((w) => <option key={w.id} value={w.id}>{w.name} ({w.size_bytes} bytes)</option>)}
            </select>
            {wordlists.length === 0 && <p className="text-xs text-amber-700 mt-1">No wordlists found in fixtures/wordlists -- see docs/WINDOWS_SETUP.md.</p>}
          </div>
        )}

        {errorMsg && <div className="text-sm text-red-700">{errorMsg}</div>}

        <div className="flex gap-3">
          <button
            onClick={startExperiment}
            disabled={!upload || status === "running" || status === "starting"}
            className="bg-teal text-white text-sm px-4 py-2 rounded-md disabled:opacity-40 focus-ring"
          >
            {status === "starting" ? "Starting..." : "Start experiment"}
          </button>
          {status === "running" && (
            <button onClick={cancel} className="text-sm px-4 py-2 rounded-md border border-slateblue/20 focus-ring">Cancel</button>
          )}
        </div>
      </div>

      {session && <EvidencePanel session={session} />}
    </div>
  );
}
