import { useEffect, useState } from "react";
import { CheckCircle2, AlertTriangle, XCircle, RefreshCw, HelpCircle } from "lucide-react";
import { api, DoctorReport } from "../api/client";

function Icon({ status }: { status: string }) {
  if (status === "passed") return <CheckCircle2 className="text-green-600" size={18} />;
  if (status === "warning") return <AlertTriangle className="text-amber-500" size={18} />;
  if (status === "manual") return <HelpCircle className="text-blue-600" size={18} />;
  return <XCircle className="text-red-600" size={18} />;
}

export default function Doctor() {
  const [report, setReport] = useState<DoctorReport | null>(null);
  const [loading, setLoading] = useState(false);

  const load = () => {
    setLoading(true);
    api.doctor().then(setReport).finally(() => setLoading(false));
  };

  useEffect(load, []);

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-navy">Environment Doctor</h1>
        <button onClick={load} className="flex items-center gap-2 text-sm bg-slateblue text-white px-3 py-1.5 rounded-md focus-ring">
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> Re-check
        </button>
      </div>
      <p className="text-sm text-slateblue/70">
        These checks are read-only and never modify your system. A Manual check requires you to confirm a VM or network setting yourself.
      </p>

      {!report && <div className="text-sm text-slateblue/60">Running checks...</div>}

      {report && (
        <div className="bg-white border border-slateblue/10 rounded-md divide-y divide-slateblue/10">
          {report.checks.map((c) => (
            <div key={c.id} className="p-4 flex items-start gap-3">
              <Icon status={c.status} />
              <div>
                <div className="font-medium text-sm">{c.label}</div>
                <div className="text-xs text-slateblue/60 mt-0.5">{c.detail}</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
