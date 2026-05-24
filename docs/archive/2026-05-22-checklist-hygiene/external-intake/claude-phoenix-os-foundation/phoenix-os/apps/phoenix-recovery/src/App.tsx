import { useState } from "react";
import { HardDrive, RotateCcw, Cpu, Shield, FileText, Flame } from "lucide-react";
import FilesystemView  from "./views/FilesystemView";
import DataRescueView  from "./views/DataRescueView";
import BootRepairView  from "./views/BootRepairView";
import SessionLogView  from "./views/SessionLogView";

const WORKFLOWS = [
  { id: "filesystem",  label: "Filesystem Repair", icon: HardDrive,   color: "#4A90D9" },
  { id: "data-rescue", label: "Data Rescue",        icon: RotateCcw,   color: "#3DB882" },
  { id: "boot-repair", label: "Boot Repair",        icon: Cpu,         color: "#F58C1F" },
  { id: "log",         label: "Session Log",        icon: FileText,    color: "#8A929E" },
] as const;

type WorkflowId = typeof WORKFLOWS[number]["id"];

export default function App() {
  const [active, setActive] = useState<WorkflowId>("filesystem");

  return (
    <div style={s.root}>
      {/* Sidebar */}
      <aside style={s.sidebar}>
        <div style={s.logo}>
          <Flame size={20} color="#D94215" strokeWidth={2.5} />
          <div>
            <div style={s.logoTitle}>PHOENIX</div>
            <div style={s.logoSub}>RECOVERY</div>
          </div>
        </div>

        <nav style={s.nav}>
          <div style={s.navSection}>WORKFLOWS</div>
          {WORKFLOWS.map(({ id, label, icon: Icon, color }) => (
            <button
              key={id}
              style={{ ...s.navItem, ...(active === id ? { ...s.navActive, borderLeftColor: color } : {}) }}
              onClick={() => setActive(id)}
            >
              <Icon size={15} color={active === id ? color : "#8A929E"} />
              <span style={{ color: active === id ? "#E8EAF0" : "#8A929E", fontSize: "13px" }}>
                {label}
              </span>
            </button>
          ))}
        </nav>

        {/* Safety reminder */}
        <div style={s.safetyBox}>
          <Shield size={13} color="#F5C842" />
          <span style={s.safetyText}>
            All destructive ops require device path confirmation.
          </span>
        </div>
      </aside>

      {/* Main */}
      <main style={s.main}>
        {active === "filesystem"  && <FilesystemView />}
        {active === "data-rescue" && <DataRescueView />}
        {active === "boot-repair" && <BootRepairView />}
        {active === "log"         && <SessionLogView />}
      </main>
    </div>
  );
}

const s: Record<string, React.CSSProperties> = {
  root:       { display: "flex", height: "100vh", width: "100vw", backgroundColor: "#0D0F12", overflow: "hidden" },
  sidebar:    { width: "210px", minWidth: "210px", backgroundColor: "#161A1F", borderRight: "1px solid #2A2F38", display: "flex", flexDirection: "column" },
  logo:       { display: "flex", alignItems: "center", gap: "10px", padding: "20px 18px 16px", borderBottom: "1px solid #2A2F38" },
  logoTitle:  { color: "#E8EAF0", fontSize: "14px", fontWeight: "700", letterSpacing: "0.16em", fontFamily: "'Rajdhani', sans-serif", lineHeight: 1 },
  logoSub:    { color: "#D94215", fontSize: "10px", letterSpacing: "0.2em", fontFamily: "'Rajdhani', sans-serif", marginTop: "2px" },
  nav:        { flex: 1, padding: "12px 8px", display: "flex", flexDirection: "column", gap: "2px" },
  navSection: { color: "#4A515C", fontSize: "10px", fontWeight: "700", letterSpacing: "0.12em", padding: "8px 12px 6px", textTransform: "uppercase" },
  navItem:    { display: "flex", alignItems: "center", gap: "10px", padding: "9px 12px", borderRadius: "6px", border: "none", borderLeft: "2px solid transparent", background: "transparent", cursor: "pointer", width: "100%", textAlign: "left" },
  navActive:  { backgroundColor: "#1E2329", paddingLeft: "10px" },
  safetyBox:  { margin: "0 10px 14px", padding: "10px 12px", backgroundColor: "#1A180A", border: "1px solid #F5C842", borderRadius: "6px", display: "flex", alignItems: "flex-start", gap: "8px" },
  safetyText: { color: "#8A929E", fontSize: "11px", lineHeight: "1.5" },
  main:       { flex: 1, overflowY: "auto", backgroundColor: "#0D0F12" },
};
