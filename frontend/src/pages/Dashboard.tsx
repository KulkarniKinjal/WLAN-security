import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { AlertTriangle, CheckCircle2, XCircle, Wifi, Terminal, UserCheck } from "lucide-react";
import { api, DashboardData } from "../api/client";
import StatusChip from "../components/StatusChip";

const moduleMeta: Record<string, { label: string; description: string; needs: string; icon: typeof Wifi; to: string }> = {
  wireless_wep: { label: "Wireless Encryption Lab", description: "Analyze an authorized capture and inspect the result.", needs: "Valid capture · Wireless tools", icon: Wifi, to: "/wireless" },
  metasploit: { label: "Metasploit Lab", description: "Run one bounded scenario against your isolated target.", needs: "Kali · Host-only target", icon: Terminal, to: "/metasploit" },
  awareness: { label: "Awareness Simulator", description: "Practice spotting suspicious captive-portal signals.", needs: "No tools required", icon: UserCheck, to: "/awareness" },
};

function ReadinessIcon({ status }: { status: string }) {
  if (status === "passed") return <CheckCircle2 className="text-green-600" size={20} />;
  if (status === "warning") return <AlertTriangle className="text-amber-500" size={20} />;
  return <XCircle className="text-red-600" size={20} />;
}

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.dashboard().then(setData).catch((e) => setError(String(e)));
  }, []);

  if (error) {
    return (
      <div className="p-8">
        <div className="bg-red-50 border border-red-200 text-red-800 rounded-md p-4 text-sm">
          Could not reach the backend ({error}). Make sure it's running at the configured API URL and reload.
        </div>
      </div>
    );
  }
  if (!data) return <div className="p-8 text-slateblue/60 text-sm">Loading dashboard...</div>;

  const totalRuns = Object.values(data.status_counts).reduce((a, b) => a + b, 0);

  return (
    <div className="p-4 sm:p-8 max-w-6xl mx-auto space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold text-navy">Dashboard</h1>
        <div className="flex items-center gap-2 text-sm">
          <ReadinessIcon status={data.environment_readiness} />
          Environment: <span className="font-semibold capitalize">{data.environment_readiness}</span>
          <Link to="/doctor" className="text-teal underline ml-2">Run doctor</Link>
        </div>
      </div>

      {totalRuns === 0 && (
        <div className="bg-iceblue border border-teal/30 rounded-md p-5 text-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div><div className="font-semibold text-navy">Your next step</div><div className="text-slateblue/70 mt-1">Start with the fictional awareness scenario; it needs no Kali tools.</div></div>
          <Link to="/awareness" className="bg-teal text-white px-4 py-2 rounded-md text-center whitespace-nowrap">Start awareness scenario</Link>
        </div>
      )}

      <section>
        <h2 className="text-sm font-semibold text-slateblue/70 uppercase tracking-wide mb-3">Modules</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Object.entries(moduleMeta).map(([key, meta]) => {
            const Icon = meta.icon;
            return (
              <Link key={key} to={meta.to} className="bg-white border border-slateblue/10 rounded-md p-5 hover:border-teal transition-colors focus-ring">
                <Icon size={20} className="text-teal mb-2" />
                <div className="font-semibold text-sm">{meta.label}</div>
                <div className="text-xs text-slateblue/70 mt-2">{meta.description}</div>
                <div className="text-[11px] text-teal mt-3">Needs: {meta.needs}</div>
              </Link>
            );
          })}
        </div>
      </section>

      <section>
        <h2 className="text-sm font-semibold text-slateblue/70 uppercase tracking-wide mb-3">Run outcomes</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {["succeeded", "failed", "cancelled", "timed_out"].map((k) => (
            <div key={k} className="bg-white border border-slateblue/10 rounded-md p-4 text-center">
              <div className="text-2xl font-semibold text-navy">{data.status_counts[k] ?? 0}</div>
              <div className="text-xs text-slateblue/60 capitalize">{k.replace("_", " ")}</div>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-sm font-semibold text-slateblue/70 uppercase tracking-wide mb-3">Recent sessions</h2>
        {data.recent_sessions.length === 0 ? (
          <div className="text-sm text-slateblue/60">No sessions yet.</div>
        ) : (
          <div className="bg-white border border-slateblue/10 rounded-md overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-iceblue/60 text-left text-xs uppercase text-slateblue/60">
                <tr><th className="p-3">Name</th><th className="p-3">Module</th><th className="p-3">Status</th><th className="p-3">Outcome</th><th className="p-3">Mode</th><th className="p-3">Created</th></tr>
              </thead>
              <tbody>
                {data.recent_sessions.map((s) => (
                  <tr key={s.id} className="border-t border-slateblue/10">
                    <td className="p-3"><Link to={`/history?id=${s.id}`} className="text-teal underline">{s.name}</Link></td>
                    <td className="p-3">{s.module}</td>
                    <td className="p-3"><StatusChip value={s.status} /></td>
                    <td className="p-3"><StatusChip value={s.outcome} /></td>
                    <td className="p-3 text-xs uppercase">{s.execution_mode}</td>
                    <td className="p-3 text-xs text-slateblue/60">{new Date(s.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section>
        <h2 className="text-sm font-semibold text-slateblue/70 uppercase tracking-wide mb-3">Findings by module</h2>
        {Object.keys(data.findings_by_module).length === 0 ? (
          <div className="text-sm text-slateblue/60">No findings recorded yet -- they appear here after you run an experiment.</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(data.findings_by_module).map(([mod, findings]) => (
              <div key={mod} className="bg-white border border-slateblue/10 rounded-md p-4">
                <div className="font-semibold text-sm mb-2">{mod}</div>
                <ul className="space-y-2">
                  {findings.map((f) => (
                    <li key={f.id} className="text-xs">
                      <span className={`status-chip ${f.severity === "finding" ? "failed" : f.severity === "warning" ? "warning" : "cancelled"}`}>{f.severity}</span>{" "}
                      <span className="font-medium">{f.title}</span>
                      <div className="text-slateblue/60">{f.summary}</div>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
