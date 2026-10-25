import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Trash2 } from "lucide-react";
import { api, SessionDetail, SessionListItem } from "../api/client";
import StatusChip from "../components/StatusChip";
import EvidencePanel from "../components/EvidencePanel";

export default function History() {
  const [params] = useSearchParams();
  const [sessions, setSessions] = useState<SessionListItem[]>([]);
  const [moduleFilter, setModuleFilter] = useState("");
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<SessionDetail | null>(null);
  const [compareIds, setCompareIds] = useState<string[]>([]);
  const [compareSessions, setCompareSessions] = useState<SessionDetail[]>([]);

  const load = () => {
    api.listSessions(moduleFilter ? { module: moduleFilter } : undefined).then(setSessions);
  };

  useEffect(load, [moduleFilter]);

  useEffect(() => {
    const id = params.get("id");
    if (id) api.getSession(id).then(setSelected);
  }, [params]);

  const filtered = sessions.filter((s) => s.name.toLowerCase().includes(search.toLowerCase()) || s.scenario_id.includes(search.toLowerCase()));

  const del = async (id: string) => {
    if (!confirm("Delete this session permanently?")) return;
    await api.deleteSession(id);
    if (selected?.id === id) setSelected(null);
    load();
  };

  const toggleCompare = (id: string) => {
    setCompareIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : prev.length < 2 ? [...prev, id] : prev));
  };

  useEffect(() => {
    if (compareIds.length === 2) {
      Promise.all(compareIds.map((id) => api.getSession(id))).then(setCompareSessions);
    } else {
      setCompareSessions([]);
    }
  }, [compareIds]);

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6">
      <h1 className="text-2xl font-semibold text-navy">Session History</h1>

      <div className="flex gap-3 items-center">
        <input placeholder="Search by name or scenario..." value={search} onChange={(e) => setSearch(e.target.value)} className="border border-slateblue/20 rounded-md px-3 py-2 text-sm flex-1 focus-ring" />
        <select value={moduleFilter} onChange={(e) => setModuleFilter(e.target.value)} className="border border-slateblue/20 rounded-md px-3 py-2 text-sm focus-ring">
          <option value="">All modules</option>
          <option value="wireless_wep">Wireless (WEP)</option>
          <option value="wireless_wpa">Wireless (WPA)</option>
          <option value="metasploit">Metasploit</option>
          <option value="awareness">Awareness</option>
        </select>
      </div>

      <p className="text-xs text-slateblue/50">Select up to two sessions with the checkboxes to compare them side by side.</p>

      <div className="bg-white border border-slateblue/10 rounded-md overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-iceblue/60 text-left text-xs uppercase text-slateblue/60">
            <tr><th className="p-3"></th><th className="p-3">Name</th><th className="p-3">Module</th><th className="p-3">Status</th><th className="p-3">Outcome</th><th className="p-3">Mode</th><th className="p-3">Created</th><th className="p-3"></th></tr>
          </thead>
          <tbody>
            {filtered.map((s) => (
              <tr key={s.id} className="border-t border-slateblue/10 hover:bg-iceblue/30">
                <td className="p-3"><input type="checkbox" checked={compareIds.includes(s.id)} onChange={() => toggleCompare(s.id)} /></td>
                <td className="p-3"><button onClick={() => api.getSession(s.id).then(setSelected)} className="text-teal underline">{s.name}</button></td>
                <td className="p-3">{s.module}</td>
                <td className="p-3"><StatusChip value={s.status} /></td>
                <td className="p-3"><StatusChip value={s.outcome} /></td>
                <td className="p-3 text-xs uppercase">{s.execution_mode}</td>
                <td className="p-3 text-xs text-slateblue/60">{new Date(s.created_at).toLocaleString()}</td>
                <td className="p-3"><button onClick={() => del(s.id)} className="text-red-600 focus-ring"><Trash2 size={14} /></button></td>
              </tr>
            ))}
            {filtered.length === 0 && <tr><td colSpan={8} className="p-6 text-center text-slateblue/50 text-sm">No sessions match.</td></tr>}
          </tbody>
        </table>
      </div>

      {compareSessions.length === 2 && (
        <div>
          <h2 className="text-sm font-semibold text-slateblue/70 uppercase tracking-wide mb-3">Comparison</h2>
          <div className="grid grid-cols-2 gap-4">
            {compareSessions.map((s) => <EvidencePanel key={s.id} session={s} />)}
          </div>
        </div>
      )}

      {selected && (
        <div>
          <h2 className="text-sm font-semibold text-slateblue/70 uppercase tracking-wide mb-3">Session detail</h2>
          <EvidencePanel session={selected} />
        </div>
      )}
    </div>
  );
}
