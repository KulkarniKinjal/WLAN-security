import { SessionDetail } from "../api/client";
import StatusChip from "./StatusChip";

export default function EvidencePanel({ session }: { session: SessionDetail }) {
  return (
    <div className="bg-white border border-slateblue/10 rounded-md divide-y divide-slateblue/10">
      <div className="p-4 flex items-center justify-between">
        <div>
          <div className="font-semibold">{session.name}</div>
          <div className="text-xs text-slateblue/60">{session.scenario_id}</div>
        </div>
        <div className="flex items-center gap-2">
          <StatusChip value={session.status} />
          <StatusChip value={session.outcome} />
          <span className={`status-chip ${session.execution_mode === "real" ? "warning" : "cancelled"}`}>
            {session.execution_mode === "real" ? "REAL" : "DEMO"}
          </span>
        </div>
      </div>

      {session.fixture_provenance && (
        <div className="p-4 text-sm">
          <span className="font-semibold">Provenance: </span>
          {session.fixture_provenance}
        </div>
      )}

      {session.explanation?.objective && (
        <div className="p-4 text-sm space-y-2">
          <div><span className="font-semibold">Objective: </span>{session.explanation.objective}</div>
          {session.explanation.proves && <div><span className="font-semibold">What this proves: </span>{session.explanation.proves}</div>}
          {session.explanation.does_not_prove && <div><span className="font-semibold text-amber-700">What this does NOT prove: </span>{session.explanation.does_not_prove}</div>}
          {session.explanation.defense && <div><span className="font-semibold">Recommended defense: </span>{session.explanation.defense}</div>}
        </div>
      )}

      <div className="p-4 text-sm">
        <div className="font-semibold mb-1">Evidence</div>
        <pre className="bg-iceblue/60 rounded p-2 text-xs overflow-x-auto max-h-64">{JSON.stringify(session.evidence, null, 2)}</pre>
      </div>

      {session.raw_log && (
        <div className="p-4 text-sm">
          <div className="font-semibold mb-1">Raw tool output (bounded)</div>
          <pre className="bg-navy text-iceblue rounded p-2 text-xs overflow-x-auto max-h-64 whitespace-pre-wrap">{session.raw_log.slice(0, 4000)}</pre>
        </div>
      )}

      {session.error_message && (
        <div className="p-4 text-sm text-red-700">
          <span className="font-semibold">Error: </span>{session.error_message}
        </div>
      )}

      <div className="p-4 flex gap-3 text-sm">
        <a className="text-teal underline" href={`http://127.0.0.1:8000/api/reports/${session.id}.pdf`} target="_blank" rel="noreferrer">Download PDF report</a>
        <a className="text-teal underline" href={`http://127.0.0.1:8000/api/reports/${session.id}.json`} target="_blank" rel="noreferrer">Download JSON</a>
      </div>
    </div>
  );
}
