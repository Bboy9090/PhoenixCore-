import { useEffect, useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import { Cpu, MemoryStick, Thermometer, Server } from "lucide-react";
import SectionHeader from "../components/SectionHeader";

interface CpuInfo {
  model_name:          string;
  core_count:          number;
  thread_count:        number;
  frequency_mhz:       number;
  usage_percent:       number;
  temperature_celsius: number | null;
}

interface MemoryInfo {
  total_bytes:      number;
  available_bytes:  number;
  used_bytes:       number;
  used_percent:     number;
  swap_total_bytes: number;
  swap_used_bytes:  number;
}

interface ThermalSensor {
  name:                string;
  temperature_celsius: number;
}

interface ThermalInfo {
  sensors: ThermalSensor[];
}

function fmt(bytes: number): string {
  if (bytes >= 1_073_741_824) return `${(bytes / 1_073_741_824).toFixed(2)} GB`;
  if (bytes >= 1_048_576)     return `${(bytes / 1_048_576).toFixed(0)} MB`;
  return `${bytes} B`;
}

export default function SystemView() {
  const [cpu,     setCpu]     = useState<CpuInfo | null>(null);
  const [mem,     setMem]     = useState<MemoryInfo | null>(null);
  const [thermal, setThermal] = useState<ThermalInfo | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [c, m, t] = await Promise.all([
          invoke<CpuInfo>("get_cpu_info"),
          invoke<MemoryInfo>("get_memory_info"),
          invoke<ThermalInfo>("get_thermal_info"),
        ]);
        setCpu(c); setMem(m); setThermal(t);
      } finally {
        setLoading(false);
      }
    };
    load();
    const id = setInterval(load, 3000);
    return () => clearInterval(id);
  }, []);

  if (loading) return <div style={s.loading}>Loading system data…</div>;

  return (
    <div style={s.page}>
      <SectionHeader
        title="System"
        subtitle="CPU, memory, and thermal sensors"
        icon={<Cpu size={18} color="#F58C1F" />}
      />

      {/* CPU */}
      <Section label="CPU" icon={<Cpu size={14} color="#F58C1F" />}>
        {cpu && (
          <>
            <Row label="Model"       value={cpu.model_name} />
            <Row label="Cores"       value={`${cpu.core_count} cores / ${cpu.thread_count} threads`} />
            <Row label="Frequency"   value={`${cpu.frequency_mhz.toFixed(0)} MHz`} />
            <Row label="Usage"       value={`${cpu.usage_percent.toFixed(1)}%`} highlight />
            {cpu.temperature_celsius != null && (
              <Row label="Temperature" value={`${cpu.temperature_celsius.toFixed(0)}°C`}
                warn={cpu.temperature_celsius > 85} />
            )}
          </>
        )}
      </Section>

      {/* Memory */}
      <Section label="Memory" icon={<MemoryStick size={14} color="#4A90D9" />}>
        {mem && (
          <>
            <Row label="Total RAM"   value={fmt(mem.total_bytes)} />
            <Row label="Used"        value={`${fmt(mem.used_bytes)} (${mem.used_percent.toFixed(1)}%)`} highlight />
            <Row label="Available"   value={fmt(mem.available_bytes)} />
            <Row label="Swap Total"  value={fmt(mem.swap_total_bytes)} />
            <Row label="Swap Used"   value={fmt(mem.swap_used_bytes)} />
          </>
        )}
      </Section>

      {/* Thermal */}
      <Section label="Thermal Sensors" icon={<Thermometer size={14} color="#F5C842" />}>
        {thermal && thermal.sensors.length > 0 ? thermal.sensors.map(s => (
          <Row
            key={s.name}
            label={s.name}
            value={`${s.temperature_celsius.toFixed(1)}°C`}
            warn={s.temperature_celsius > 85}
          />
        )) : (
          <div style={s.empty}>No thermal sensors available</div>
        )}
      </Section>
    </div>
  );
}

function Section({ label, icon, children }: { label: string; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <div style={s.section}>
      <div style={s.sectionHeader}>
        {icon}
        <span style={s.sectionLabel}>{label}</span>
      </div>
      <div style={s.sectionBody}>{children}</div>
    </div>
  );
}

function Row({ label, value, highlight, warn }: { label: string; value: string; highlight?: boolean; warn?: boolean }) {
  return (
    <div style={s.row}>
      <span style={s.rowLabel}>{label}</span>
      <span style={{
        ...s.rowValue,
        color: warn ? "#E03A3A" : highlight ? "#F58C1F" : "#E8EAF0",
      }}>{value}</span>
    </div>
  );
}

const s: Record<string, React.CSSProperties> = {
  page:        { padding: "28px 32px", height: "100%", overflowY: "auto" },
  loading:     { padding: "40px", color: "#8A929E" },
  empty:       { color: "#4A515C", fontSize: "12px", padding: "8px 0" },
  section:     { backgroundColor: "#161A1F", border: "1px solid #2A2F38", borderRadius: "8px", marginBottom: "16px", overflow: "hidden" },
  sectionHeader: { display: "flex", alignItems: "center", gap: "8px", padding: "12px 16px", borderBottom: "1px solid #2A2F38", backgroundColor: "#1E2329" },
  sectionLabel:{ color: "#E8EAF0", fontSize: "13px", fontWeight: "600" },
  sectionBody: { padding: "4px 0" },
  row:         { display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 16px", borderBottom: "1px solid #1E2329" },
  rowLabel:    { color: "#8A929E", fontSize: "12px" },
  rowValue:    { fontSize: "12px", fontFamily: "'IBM Plex Mono', monospace" },
};
