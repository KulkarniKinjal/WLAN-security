import { NavLink, Outlet } from "react-router-dom";
import { ShieldCheck, LayoutDashboard, Stethoscope, Wifi, Terminal, UserCheck, History, Lock } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "../api/client";

const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/doctor", label: "Environment Doctor", icon: Stethoscope },
  { to: "/wireless", label: "Wireless Lab", icon: Wifi },
  { to: "/metasploit", label: "Metasploit Lab", icon: Terminal },
  { to: "/awareness", label: "Awareness Simulator", icon: UserCheck },
  { to: "/history", label: "Session History", icon: History },
];

export default function Layout() {
  const [mode, setMode] = useState<string>("...");

  useEffect(() => {
    api.health().then((h) => setMode(h.execution_mode)).catch(() => setMode("unreachable"));
  }, []);

  return (
    <div className="flex min-h-screen">
      <aside className="w-64 shrink-0 bg-navy text-iceblue flex flex-col">
        <div className="px-5 py-5 flex items-center gap-2 border-b border-white/10">
          <ShieldCheck size={22} className="text-teal" />
          <div>
            <div className="font-semibold leading-tight">WLAN AttackLab</div>
            <div className="text-xs text-iceblue/60">Guided WLAN security lab</div>
          </div>
        </div>
        <nav className="flex-1 py-3">
          {navItems.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex items-center gap-3 px-5 py-2.5 text-sm focus-ring ${
                  isActive ? "bg-slateblue text-white border-l-4 border-teal" : "text-iceblue/80 hover:bg-slateblue/60 border-l-4 border-transparent"
                }`
              }
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="px-5 py-4 border-t border-white/10 text-xs flex items-center gap-2">
          <Lock size={14} className="text-teal" />
          <span>
            Mode:{" "}
            <span className={`font-semibold ${mode === "real" ? "text-amber-300" : "text-teal"}`}>
              {mode === "..." ? "checking..." : mode.toUpperCase()}
            </span>
          </span>
        </div>
      </aside>
      <main className="flex-1 bg-offwhite min-h-screen">
        <Outlet />
      </main>
    </div>
  );
}
