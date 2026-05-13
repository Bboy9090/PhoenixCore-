import { useEffect, useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import { HardDrive, RefreshCw, AlertTriangle, CheckCircle, XCircle, HelpCircle } from "lucide-react";
import SectionHeader from "../components/SectionHeader";

interface DiskInfo {
  device:        string;
  model:         string;
  serial:        string;
  size_human:    string;
  bus_type:      string;
  smart_available: boolean;
  health_status: "Passed" | "Warning" | "Failed" | "Unknown";
  partitions:    PartitionInfo[];
}

interface PartitionInfo {
  device:      string;
  size_human:  string;
  filesystem:  string | null;
  mountpoint:  string | null;
  label:       string | null;
}

const HEALTH_CONFIG = {
  Passed:  { color: "#3DB882", Icon: CheckCircle,   label: "Healthy"  },
  Warning: { color: "#F5C842", Icon: AlertTriangle, label: "Warning"  },
  Failed:  { color: "#E03A3A", Icon: XCircle,       label: "Failed"   },
  Unknown: { color: "#8A929E", Icon: HelpCircle,    label: "Unknown"  },
};

export default function DisksView() {
  const [disks,    setDisks]    = useState<DiskInfo[]>([]);
  const [loading,  setLoading]  = useState(true);
  const [error,    setError]    = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);

  const loadDisks = async () => {
    setLoading(true);
    try {
      const result = await invoke<DiskInfo[]>("list_disks");
      setDisks(result);
      setError(null);
      if (result.length > 0 && !selected) {
        setSelected(result[0].device);
      }
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadDisks(); }, []);

  const selectedDisk = disks.find(d => d.device === selected);

  return (
    <div style={styles.page}>
      <SectionHeader
        title="Disks"
        subtitle="S.M.A.R.T. health, partition layout, and device details"
        icon={<HardDrive size={18} color="#F58C1F" />}
        action={
          <button style={styles.refreshBtn} onClick={loadDisks} disabled={loading}>
            <RefreshCw size={14} style={{ animation: loading ? "spin 1s linear infinite" : "none" }} />
            Refresh
          </button>
        }
      />

      {/* Safety notice */}
      <div style={styles.safetyNotice}>
        <AlertTriangle size={13} color="#F5C842" />
        <span>This view is read-only. Disk operations are available in Phoenix Recovery.</span>
      </div>

      {error && (
        <div style={styles.error}>
          <XCircle size={14} /> Error: {error}
        </div>
      )}

      {!loading && disks.length === 0 && !error && (
        <div style={styles.empty}>
          No physical disks detected. This may occur in some virtual environments.
        </div>
      )}

      <div style={styles.layout}>
        {/* Disk list */}
        <div style={styles.diskList}>
          {disks.map(disk => {
            const { color, Icon, label } = HEALTH_CONFIG[disk.health_status];
            return (
              <button
                key={disk.device}
                style={{
                  ...styles.diskItem,
                  ...(selected === disk.device ? styles.diskItemActive : {}),
                }}
                onClick={() => setSelected(disk.device)}
              >
                <div style={styles.diskItemHeader}>
                  <HardDrive size={15} color={color} />
                  <span style={styles.diskDevice}>{disk.device}</span>
                  <span style={{ ...styles.healthBadge, color, borderColor: color }}>
                    <Icon size={11} /> {label}
                  </span>
                </div>
                <div style={styles.diskModel}>{disk.model || "Unknown Model"}</div>
                <div style={styles.diskMeta}>
                  {disk.size_human} · {disk.bus_type.toUpperCase()}
                </div>
              </button>
            );
          })}
        </div>

        {/* Disk detail panel */}
        {selectedDisk && (
          <div style={styles.detailPanel}>
            <DiskDetail disk={selectedDisk} />
          </div>
        )}
      </div>
    </div>
  );
}

function DiskDetail({ disk }: { disk: DiskInfo }) {
  const { color, Icon, label } = HEALTH_CONFIG[disk.health_status];

  return (
    <div>
      {/* Header */}
      <div style={detail.header}>
        <div>
          <div style={detail.devicePath}>{disk.device}</div>
          <div style={detail.model}>{disk.model || "Unknown Model"}</div>
        </div>
        <div style={{ ...detail.healthPill, backgroundColor: color + "20", border: `1px solid ${color}` }}>
          <Icon size={14} color={color} />
          <span style={{ color }}>{label}</span>
        </div>
      </div>

      {/* Metadata table */}
      <table style={detail.table}>
        <tbody>
          <MetaRow label="Serial"    value={disk.serial    || "—"} />
          <MetaRow label="Capacity"  value={disk.size_human || "—"} />
          <MetaRow label="Interface" value={disk.bus_type.toUpperCase() || "—"} />
          <MetaRow label="S.M.A.R.T." value={disk.smart_available ? "Available" : "Not available"} />
        </tbody>
      </table>

      {/* Partitions */}
      <div style={detail.sectionLabel}>PARTITION TABLE</div>
      {disk.partitions.length === 0 ? (
        <div style={detail.empty}>No partitions detected</div>
      ) : (
        <div style={detail.partitionList}>
          {disk.partitions.map(p => (
            <div key={p.device} style={detail.partition}>
              <div style={detail.partDevice}>{p.device}</div>
              <div style={detail.partMeta}>
                <span>{p.size_human}</span>
                {p.filesystem && <span style={detail.tag}>{p.filesystem}</span>}
                {p.label      && <span style={detail.tag}>{p.label}</span>}
                {p.mountpoint && <span style={{ ...detail.tag, color: "#4A90D9", borderColor: "#4A90D9" }}>{p.mountpoint}</span>}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* SMART data placeholder */}
      {disk.smart_available && (
        <>
          <div style={detail.sectionLabel}>S.M.A.R.T. ATTRIBUTES</div>
          <div style={detail.empty}>
            S.M.A.R.T. attribute parsing coming in Phase 1.
            <br />
            Run <code style={detail.code}>sudo smartctl -a {disk.device}</code> in terminal for full data.
          </div>
        </>
      )}
    </div>
  );
}

function MetaRow({ label, value }: { label: string; value: string }) {
  return (
    <tr>
      <td style={detail.tdLabel}>{label}</td>
      <td style={detail.tdValue}>{value}</td>
    </tr>
  );
}

const styles: Record<string, React.CSSProperties> = {
  page:         { padding: "28px 32px", height: "100%", overflowY: "auto" },
  safetyNotice: { display: "flex", alignItems: "center", gap: "8px", backgroundColor: "#1A180A", border: "1px solid #F5C842", borderRadius: "6px", padding: "8px 12px", marginBottom: "20px", color: "#F5C842", fontSize: "12px" },
  error:        { display: "flex", alignItems: "center", gap: "8px", color: "#E03A3A", backgroundColor: "#1A0A0A", border: "1px solid #E03A3A", borderRadius: "6px", padding: "8px 12px", marginBottom: "16px", fontSize: "12px" },
  empty:        { color: "#8A929E", padding: "24px", textAlign: "center" },
  layout:       { display: "grid", gridTemplateColumns: "260px 1fr", gap: "16px", alignItems: "start" },
  diskList:     { display: "flex", flexDirection: "column", gap: "6px" },
  diskItem:     { backgroundColor: "#161A1F", border: "1px solid #2A2F38", borderRadius: "8px", padding: "12px 14px", cursor: "pointer", textAlign: "left", transition: "border-color 0.15s" },
  diskItemActive: { borderColor: "#F58C1F", backgroundColor: "#1A1F26" },
  diskItemHeader: { display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" },
  diskDevice:   { color: "#E8EAF0", fontSize: "13px", fontWeight: "600", flex: 1 },
  healthBadge:  { display: "flex", alignItems: "center", gap: "4px", fontSize: "10px", border: "1px solid", borderRadius: "4px", padding: "2px 6px" },
  diskModel:    { color: "#8A929E", fontSize: "11px", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" },
  diskMeta:     { color: "#4A515C", fontSize: "11px", marginTop: "2px" },
  detailPanel:  { backgroundColor: "#161A1F", border: "1px solid #2A2F38", borderRadius: "8px", padding: "20px" },
  refreshBtn:   { display: "flex", alignItems: "center", gap: "6px", backgroundColor: "#1E2329", border: "1px solid #2A2F38", borderRadius: "6px", padding: "6px 12px", color: "#E8EAF0", fontSize: "12px", cursor: "pointer" },
};

const detail: Record<string, React.CSSProperties> = {
  header:      { display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" },
  devicePath:  { color: "#E8EAF0", fontWeight: "700", fontSize: "15px", fontFamily: "'IBM Plex Mono', monospace" },
  model:       { color: "#8A929E", fontSize: "12px", marginTop: "2px" },
  healthPill:  { display: "flex", alignItems: "center", gap: "6px", borderRadius: "6px", padding: "6px 10px", fontSize: "13px" },
  table:       { width: "100%", borderCollapse: "collapse", marginBottom: "20px" },
  tdLabel:     { color: "#8A929E", fontSize: "11px", padding: "5px 0", width: "100px", textTransform: "uppercase", letterSpacing: "0.06em" },
  tdValue:     { color: "#E8EAF0", fontSize: "12px", padding: "5px 0", fontFamily: "'IBM Plex Mono', monospace" },
  sectionLabel:{ color: "#4A515C", fontSize: "10px", fontWeight: "700", letterSpacing: "0.12em", textTransform: "uppercase", marginBottom: "10px", marginTop: "20px" },
  empty:       { color: "#8A929E", fontSize: "12px", padding: "12px 0", lineHeight: "1.7" },
  partitionList:{ display: "flex", flexDirection: "column", gap: "6px" },
  partition:   { backgroundColor: "#1E2329", borderRadius: "6px", padding: "10px 12px" },
  partDevice:  { color: "#E8EAF0", fontSize: "12px", fontFamily: "'IBM Plex Mono', monospace", marginBottom: "4px" },
  partMeta:    { display: "flex", gap: "6px", flexWrap: "wrap" },
  tag:         { color: "#8A929E", border: "1px solid #2A2F38", borderRadius: "3px", padding: "1px 6px", fontSize: "10px" },
  code:        { backgroundColor: "#1E2329", padding: "2px 6px", borderRadius: "3px", fontSize: "11px", color: "#F58C1F", fontFamily: "'IBM Plex Mono', monospace" },
};
