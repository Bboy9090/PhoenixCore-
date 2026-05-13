import { useEffect, useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import { Activity, HardDrive, Cpu, Thermometer, Wifi, Clock } from "lucide-react";
import StatCard   from "../components/StatCard";
import SectionHeader from "../components/SectionHeader";

interface SystemInfo {
  hostname:        string;
  os_name:         string;
  os_version:      string;
  kernel_version:  string;
  uptime_seconds:  number;
  cpu_count:       number;
  total_ram_bytes: number;
}

interface MemoryInfo {
  total_bytes:     number;
  available_bytes: number;
  used_bytes:      number;
  used_percent:    number;
}

interface CpuInfo {
  model_name:          string;
  usage_percent:       number;
  temperature_celsius: number | null;
}

function formatUptime(seconds: number): string {
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (d > 0) return `${d}d ${h}h ${m}m`;
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

function formatBytes(bytes: number): string {
  if (bytes >= 1_073_741_824) return `${(bytes / 1_073_741_824).toFixed(1)} GB`;
  if (bytes >= 1_048_576)     return `${(bytes / 1_048_576).toFixed(0)} MB`;
  return `${bytes} B`;
}

export default function DashboardView() {
  const [sysInfo, setSysInfo] = useState<SystemInfo | null>(null);
  const [memInfo, setMemInfo] = useState<MemoryInfo | null>(null);
  const [cpuInfo, setCpuInfo] = useState<CpuInfo | null>(null);
  const [error,   setError]   = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      const [sys, mem, cpu] = await Promise.all([
        invoke<SystemInfo>("get_system_info"),
        invoke<MemoryInfo>("get_memory_info"),
        invoke<CpuInfo>("get_cpu_info"),
      ]);
      setSysInfo(sys);
      setMemInfo(mem);
      setCpuInfo(cpu);
      setError(null);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000); // Refresh every 5s
    return () => clearInterval(interval);
  }, []);

  if (loading) return <LoadingState />;
  if (error)   return <ErrorState message={error} />;

  return (
    <div style={styles.page}>
      <SectionHeader
        title="Dashboard"
        subtitle={sysInfo ? `${sysInfo.hostname} — ${sysInfo.os_name}` : ""}
        icon={<Activity size={18} color="#F58C1F" />}
      />

      {/* ---- System identity ---- */}
      <div style={styles.infoRow}>
        <InfoChip label="Kernel"   value={sysInfo?.kernel_version ?? "—"} />
        <InfoChip label="CPUs"     value={`${sysInfo?.cpu_count ?? "—"} threads`} />
        <InfoChip label="RAM"      value={formatBytes(sysInfo?.total_ram_bytes ?? 0)} />
        <InfoChip label="Uptime"   value={formatUptime(sysInfo?.uptime_seconds ?? 0)} icon={<Clock size={13} />} />
      </div>

      {/* ---- Stat cards grid ---- */}
      <div style={styles.grid}>
        <StatCard
          icon={<Cpu size={18} color="#F58C1F" />}
          label="CPU Usage"
          value={`${cpuInfo?.usage_percent.toFixed(1) ?? "—"}%`}
          detail={cpuInfo?.model_name ?? ""}
          barValue={cpuInfo?.usage_percent}
          barColor="#F58C1F"
        />
        <StatCard
          icon={<Activity size={18} color="#4A90D9" />}
          label="Memory"
          value={`${memInfo?.used_percent.toFixed(1) ?? "—"}%`}
          detail={`${formatBytes(memInfo?.used_bytes ?? 0)} / ${formatBytes(memInfo?.total_bytes ?? 0)}`}
          barValue={memInfo?.used_percent}
          barColor={
            (memInfo?.used_percent ?? 0) > 85 ? "#E03A3A" :
            (memInfo?.used_percent ?? 0) > 70 ? "#F5C842" : "#4A90D9"
          }
        />
        <StatCard
          icon={<Thermometer size={18} color={
            (cpuInfo?.temperature_celsius ?? 0) > 85 ? "#E03A3A" :
            (cpuInfo?.temperature_celsius ?? 0) > 70 ? "#F5C842" : "#3DB882"
          } />}
          label="CPU Temp"
          value={cpuInfo?.temperature_celsius != null
            ? `${cpuInfo.temperature_celsius.toFixed(0)}°C`
            : "N/A"}
          detail={
            (cpuInfo?.temperature_celsius ?? 0) > 85 ? "Critical — check cooling" :
            (cpuInfo?.temperature_celsius ?? 0) > 70 ? "Warm — monitor" : "Normal"
          }
        />
        <StatCard
          icon={<HardDrive size={18} color="#3DB882" />}
          label="Disk Health"
          value="Scanning…"
          detail="Open Disks for full S.M.A.R.T. data"
          barColor="#3DB882"
        />
      </div>

      {/* ---- Quick launch ---- */}
      <div style={styles.section}>
        <h3 style={styles.sectionTitle}>Quick Actions</h3>
        <div style={styles.actionGrid}>
          <QuickAction label="Disk Health Scan"     desc="Run S.M.A.R.T. on all drives"       />
          <QuickAction label="Memory Test"          desc="Launch memtest in terminal"           />
          <QuickAction label="Network Diagnostics"  desc="Ping, trace, interface status"       />
          <QuickAction label="System Report"        desc="Export full hardware/OS report"       />
          <QuickAction label="Open Terminal"        desc="Konsole with phoenix environment"     />
          <QuickAction label="GParted"              desc="Visual disk partition editor"          />
        </div>
      </div>
    </div>
  );
}

// ---- Sub-components ----

function InfoChip({ label, value, icon }: { label: string; value: string; icon?: React.ReactNode }) {
  return (
    <div style={chipStyles.chip}>
      {icon && <span style={{ opacity: 0.6 }}>{icon}</span>}
      <span style={chipStyles.label}>{label}</span>
      <span style={chipStyles.value}>{value}</span>
    </div>
  );
}

function QuickAction({ label, desc }: { label: string; desc: string }) {
  const [hovered, setHovered] = useState(false);
  return (
    <button
      style={{ ...actionStyles.btn, ...(hovered ? actionStyles.btnHover : {}) }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <span style={actionStyles.label}>{label}</span>
      <span style={actionStyles.desc}>{desc}</span>
    </button>
  );
}

function LoadingState() {
  return (
    <div style={{ padding: "40px", color: "#8A929E" }}>
      Loading system information…
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div style={{ padding: "40px", color: "#E03A3A" }}>
      <strong>Error loading system data:</strong>
      <pre style={{ marginTop: "8px", fontSize: "12px" }}>{message}</pre>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  page:        { padding: "28px 32px", height: "100%", overflowY: "auto" },
  infoRow:     { display: "flex", gap: "8px", flexWrap: "wrap", margin: "16px 0 24px" },
  grid:        { display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: "12px", marginBottom: "28px" },
  section:     { marginTop: "8px" },
  sectionTitle:{ color: "#8A929E", fontSize: "11px", fontWeight: "600", letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: "12px" },
  actionGrid:  { display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: "8px" },
};

const chipStyles: Record<string, React.CSSProperties> = {
  chip:  { display: "flex", alignItems: "center", gap: "6px", backgroundColor: "#161A1F", border: "1px solid #2A2F38", borderRadius: "6px", padding: "5px 12px" },
  label: { color: "#8A929E", fontSize: "11px" },
  value: { color: "#E8EAF0", fontSize: "12px", fontWeight: "500" },
};

const actionStyles: Record<string, React.CSSProperties> = {
  btn:      { display: "flex", flexDirection: "column", alignItems: "flex-start", gap: "3px", backgroundColor: "#161A1F", border: "1px solid #2A2F38", borderRadius: "6px", padding: "12px 14px", cursor: "pointer", transition: "border-color 0.15s, background 0.15s", width: "100%" },
  btnHover: { borderColor: "#F58C1F", backgroundColor: "#1A1F26" },
  label:    { color: "#E8EAF0", fontSize: "13px", fontWeight: "500" },
  desc:     { color: "#8A929E", fontSize: "11px" },
};
