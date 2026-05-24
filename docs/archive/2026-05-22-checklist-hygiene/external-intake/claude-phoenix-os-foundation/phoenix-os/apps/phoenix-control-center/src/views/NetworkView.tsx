import { useEffect, useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import { Network, Wifi, Ethernet, Globe, RefreshCw } from "lucide-react";
import SectionHeader from "../components/SectionHeader";

interface NetworkInterface {
  name:        string;
  kind:        "Ethernet" | "Wifi" | "Loopback" | "Virtual" | "Unknown";
  state:       "Up" | "Down" | "Unknown";
  mac_address: string | null;
  ipv4:        string[];
  ipv6:        string[];
  rx_bytes:    number;
  tx_bytes:    number;
  speed_mbps:  number | null;
}

interface NetworkStatus {
  interfaces:         NetworkInterface[];
  default_route:      string | null;
  dns_servers:        string[];
  internet_reachable: boolean;
}

function fmtBytes(b: number): string {
  if (b >= 1_073_741_824) return `${(b / 1_073_741_824).toFixed(2)} GB`;
  if (b >= 1_048_576)     return `${(b / 1_048_576).toFixed(1)} MB`;
  if (b >= 1_024)         return `${(b / 1_024).toFixed(0)} KB`;
  return `${b} B`;
}

export default function NetworkView() {
  const [status, setStatus] = useState<NetworkStatus | null>(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const s = await invoke<NetworkStatus>("get_network_status");
      setStatus(s);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  if (loading) return <div style={s.loading}>Scanning network interfaces…</div>;

  const physicalIfaces = status?.interfaces.filter(i => i.kind !== "Loopback" && i.kind !== "Virtual") ?? [];

  return (
    <div style={s.page}>
      <SectionHeader
        title="Network"
        subtitle="Interfaces, routing, and connectivity"
        icon={<Network size={18} color="#F58C1F" />}
        action={
          <button style={s.refreshBtn} onClick={load}>
            <RefreshCw size={14} />
            Refresh
          </button>
        }
      />

      {/* Internet status pill */}
      <div style={{
        ...s.internetPill,
        backgroundColor: status?.internet_reachable ? "#0A1F14" : "#1A0A0A",
        borderColor:     status?.internet_reachable ? "#3DB882" : "#E03A3A",
      }}>
        <Globe size={14} color={status?.internet_reachable ? "#3DB882" : "#E03A3A"} />
        <span style={{ color: status?.internet_reachable ? "#3DB882" : "#E03A3A" }}>
          {status?.internet_reachable ? "Internet reachable" : "No internet connection"}
        </span>
        {status?.default_route && (
          <span style={s.routeText}>via {status.default_route}</span>
        )}
      </div>

      {/* Interface cards */}
      <div style={s.ifaceGrid}>
        {physicalIfaces.map(iface => (
          <InterfaceCard key={iface.name} iface={iface} />
        ))}
        {physicalIfaces.length === 0 && (
          <div style={s.empty}>No physical network interfaces found.</div>
        )}
      </div>

      {/* DNS */}
      <div style={s.section}>
        <div style={s.sectionLabel}>DNS SERVERS</div>
        {status?.dns_servers.length ? (
          status.dns_servers.map(dns => (
            <div key={dns} style={s.dnsEntry}>{dns}</div>
          ))
        ) : (
          <div style={s.empty}>No DNS servers configured</div>
        )}
      </div>
    </div>
  );
}

function InterfaceCard({ iface }: { iface: NetworkInterface }) {
  const isUp = iface.state === "Up";
  return (
    <div style={{ ...s.card, borderColor: isUp ? "#2A2F38" : "#1E2329" }}>
      <div style={s.cardHeader}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          {iface.kind === "Wifi"
            ? <Wifi size={16} color={isUp ? "#F58C1F" : "#4A515C"} />
            : <Network size={16} color={isUp ? "#4A90D9" : "#4A515C"} />
          }
          <span style={{ ...s.ifaceName, color: isUp ? "#E8EAF0" : "#8A929E" }}>{iface.name}</span>
          <span style={{ ...s.kindBadge }}>{iface.kind}</span>
        </div>
        <span style={{
          ...s.stateBadge,
          color: isUp ? "#3DB882" : "#E03A3A",
          borderColor: isUp ? "#3DB882" : "#E03A3A",
        }}>{iface.state}</span>
      </div>

      {iface.mac_address && <div style={s.mac}>{iface.mac_address}</div>}

      {iface.ipv4.length > 0 && (
        <div style={s.addrBlock}>
          {iface.ipv4.map(ip => <div key={ip} style={s.addr}>{ip}</div>)}
          {iface.ipv6.map(ip => <div key={ip} style={{ ...s.addr, color: "#4A515C" }}>{ip}</div>)}
        </div>
      )}

      <div style={s.stats}>
        <span>↓ {fmtBytes(iface.rx_bytes)}</span>
        <span>↑ {fmtBytes(iface.tx_bytes)}</span>
        {iface.speed_mbps && <span>{iface.speed_mbps} Mbps</span>}
      </div>
    </div>
  );
}

const s: Record<string, React.CSSProperties> = {
  page:        { padding: "28px 32px", height: "100%", overflowY: "auto" },
  loading:     { padding: "40px", color: "#8A929E" },
  empty:       { color: "#4A515C", fontSize: "12px", padding: "8px 0" },
  internetPill:{ display: "flex", alignItems: "center", gap: "8px", border: "1px solid", borderRadius: "8px", padding: "10px 14px", marginBottom: "20px", fontSize: "13px" },
  routeText:   { color: "#4A515C", fontSize: "11px", marginLeft: "8px", fontFamily: "'IBM Plex Mono', monospace" },
  ifaceGrid:   { display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: "12px", marginBottom: "24px" },
  card:        { backgroundColor: "#161A1F", border: "1px solid", borderRadius: "8px", padding: "14px 16px" },
  cardHeader:  { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" },
  ifaceName:   { fontSize: "14px", fontWeight: "600", fontFamily: "'IBM Plex Mono', monospace" },
  kindBadge:   { color: "#4A515C", fontSize: "10px", backgroundColor: "#1E2329", borderRadius: "3px", padding: "2px 6px" },
  stateBadge:  { fontSize: "11px", border: "1px solid", borderRadius: "4px", padding: "2px 7px" },
  mac:         { color: "#4A515C", fontSize: "11px", fontFamily: "'IBM Plex Mono', monospace", marginBottom: "8px" },
  addrBlock:   { marginBottom: "10px" },
  addr:        { color: "#E8EAF0", fontSize: "12px", fontFamily: "'IBM Plex Mono', monospace" },
  stats:       { display: "flex", gap: "16px", color: "#8A929E", fontSize: "11px", borderTop: "1px solid #2A2F38", paddingTop: "8px", marginTop: "4px" },
  section:     { backgroundColor: "#161A1F", border: "1px solid #2A2F38", borderRadius: "8px", padding: "14px 16px" },
  sectionLabel:{ color: "#4A515C", fontSize: "10px", fontWeight: "700", letterSpacing: "0.12em", textTransform: "uppercase", marginBottom: "10px" },
  dnsEntry:    { color: "#E8EAF0", fontSize: "12px", fontFamily: "'IBM Plex Mono', monospace", padding: "4px 0" },
  refreshBtn:  { display: "flex", alignItems: "center", gap: "6px", backgroundColor: "#1E2329", border: "1px solid #2A2F38", borderRadius: "6px", padding: "6px 12px", color: "#E8EAF0", fontSize: "12px", cursor: "pointer" },
};
