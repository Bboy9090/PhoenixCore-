import { useState } from "react";
import { HardDrive, Cpu, Network, Wrench, Flame, Activity } from "lucide-react";
import DashboardView  from "./views/DashboardView";
import DisksView      from "./views/DisksView";
import SystemView     from "./views/SystemView";
import NetworkView    from "./views/NetworkView";
import RepairView     from "./views/RepairView";

// ---- Navigation items ----
const NAV_ITEMS = [
  { id: "dashboard", label: "Dashboard",  icon: Activity   },
  { id: "disks",     label: "Disks",      icon: HardDrive  },
  { id: "system",    label: "System",     icon: Cpu        },
  { id: "network",   label: "Network",    icon: Network    },
  { id: "repair",    label: "Repair",     icon: Wrench     },
] as const;

type ViewId = typeof NAV_ITEMS[number]["id"];

export default function App() {
  const [activeView, setActiveView] = useState<ViewId>("dashboard");

  return (
    <div style={styles.root}>
      {/* ---- Sidebar ---- */}
      <aside style={styles.sidebar}>
        {/* Logo */}
        <div style={styles.logoArea}>
          <Flame size={22} color="#F58C1F" strokeWidth={2.5} />
          <span style={styles.logoText}>PHOENIX</span>
        </div>

        {/* Nav */}
        <nav style={styles.nav}>
          {NAV_ITEMS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              style={{
                ...styles.navItem,
                ...(activeView === id ? styles.navItemActive : {}),
              }}
              onClick={() => setActiveView(id)}
            >
              <Icon
                size={17}
                color={activeView === id ? "#F58C1F" : "#8A929E"}
                strokeWidth={activeView === id ? 2.5 : 2}
              />
              <span style={{
                ...styles.navLabel,
                color: activeView === id ? "#E8EAF0" : "#8A929E",
              }}>
                {label}
              </span>
            </button>
          ))}
        </nav>

        {/* Version footer */}
        <div style={styles.sidebarFooter}>
          <span style={styles.versionText}>Phoenix OS v0.1.0-alpha</span>
        </div>
      </aside>

      {/* ---- Main content ---- */}
      <main style={styles.main}>
        {activeView === "dashboard" && <DashboardView />}
        {activeView === "disks"     && <DisksView />}
        {activeView === "system"    && <SystemView />}
        {activeView === "network"   && <NetworkView />}
        {activeView === "repair"    && <RepairView />}
      </main>
    </div>
  );
}

// ---- Inline styles using Phoenix design tokens ----
const styles: Record<string, React.CSSProperties> = {
  root: {
    display:         "flex",
    height:          "100vh",
    width:           "100vw",
    backgroundColor: "#0D0F12",
    fontFamily:      "'IBM Plex Mono', 'Courier New', monospace",
    overflow:        "hidden",
  },
  sidebar: {
    width:           "200px",
    minWidth:        "200px",
    backgroundColor: "#161A1F",
    borderRight:     "1px solid #2A2F38",
    display:         "flex",
    flexDirection:   "column",
  },
  logoArea: {
    display:        "flex",
    alignItems:     "center",
    gap:            "10px",
    padding:        "20px 20px 16px",
    borderBottom:   "1px solid #2A2F38",
  },
  logoText: {
    color:          "#E8EAF0",
    fontSize:       "15px",
    fontWeight:     "700",
    letterSpacing:  "0.18em",
    fontFamily:     "'Rajdhani', sans-serif",
  },
  nav: {
    display:        "flex",
    flexDirection:  "column",
    gap:            "2px",
    padding:        "12px 8px",
    flex:           1,
  },
  navItem: {
    display:        "flex",
    alignItems:     "center",
    gap:            "10px",
    padding:        "9px 12px",
    borderRadius:   "6px",
    border:         "none",
    background:     "transparent",
    cursor:         "pointer",
    width:          "100%",
    textAlign:      "left",
    transition:     "background 0.15s",
  },
  navItemActive: {
    backgroundColor: "#1E2329",
    borderLeft:      "2px solid #F58C1F",
    paddingLeft:     "10px",
  },
  navLabel: {
    fontSize:       "13px",
    fontWeight:     "500",
  },
  sidebarFooter: {
    padding:        "12px 16px",
    borderTop:      "1px solid #2A2F38",
  },
  versionText: {
    color:          "#4A515C",
    fontSize:       "11px",
  },
  main: {
    flex:           1,
    overflow:       "auto",
    backgroundColor: "#0D0F12",
  },
};
