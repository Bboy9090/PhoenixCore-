import React, { useEffect, useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";

interface KeyInfo {
  present:              boolean;
  device_path:          string | null;
  mount_path:           string | null;
  serial:               string | null;
  firmware_version:     string | null;
  storage_total_bytes:  number | null;
  storage_free_bytes:   number | null;
}

function fmtBytes(n: number | null): string {
  if (!n) return "—";
  if (n >= 1e9) return `${(n / 1e9).toFixed(1)} GB`;
  if (n >= 1e6) return `${(n / 1e6).toFixed(0)} MB`;
  return `${n} B`;
}

export default function App() {
  const [key, setKey] = useState<KeyInfo | null>(null);

  const refresh = async () => {
    const k = await invoke<KeyInfo>("get_key_info");
    setKey(k);
  };

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 2000);

    // Listen for udev events
    const unlisten1 = listen("phoenix-key-inserted", (e) => setKey(e.payload as KeyInfo));
    const unlisten2 = listen("phoenix-key-removed",  () => refresh());

    return () => {
      clearInterval(interval);
      unlisten1.then(f => f());
      unlisten2.then(f => f());
    };
  }, []);

  return (
    <div style={s.root}>
      {/* Header */}
      <div style={s.header}>
        <div style={s.flame}>🔥</div>
        <div>
          <div style={s.title}>BOOTFORGE</div>
          <div style={s.sub}>Phoenix Key Manager</div>
        </div>
      </div>

      {/* Key status */}
      <div style={{ ...s.keyCard, borderColor: key?.present ? "#F58C1F" : "#2A2F38" }}>
        <div style={s.keyDot(key?.present ?? false)} />
        <div style={s.keyInfo}>
          <div style={{ color: key?.present ? "#F58C1F" : "#4A515C", fontWeight: 700, fontSize: "15px" }}>
            {key?.present ? "Phoenix Key Connected" : "No Phoenix Key Detected"}
          </div>
          {key?.present && (
            <div style={s.keyMeta}>
              {key.serial      && <MetaRow label="Serial"  value={key.serial} />}
              {key.mount_path  && <MetaRow label="Mount"   value={key.mount_path} />}
              {key.storage_total_bytes != null && (
                <MetaRow
                  label="Storage"
                  value={`${fmtBytes(key.storage_free_bytes)} free / ${fmtBytes(key.storage_total_bytes)}`}
                />
              )}
              {key.firmware_version && <MetaRow label="FW" value={key.firmware_version} />}
            </div>
          )}
          {!key?.present && (
            <div style={{ color: "#4A515C", fontSize: "12px", marginTop: "6px" }}>
              Insert your Phoenix Key USB to begin a repair session.
            </div>
          )}
        </div>
      </div>

      {/* Actions */}
      <div style={s.actions}>
        <Action
          label="Phoenix Control Center"
          desc="Diagnostics and system overview"
          disabled={false}
          onClick={() => invoke("launch_control_center")}
          color="#F58C1F"
        />
        <Action
          label="Phoenix Recovery"
          desc="Data rescue and filesystem repair"
          disabled={false}
          onClick={() => invoke("launch_recovery")}
          color="#3DB882"
        />
        <Action
          label="View Session Log"
          desc="Sessions stored on the Phoenix Key"
          disabled={!key?.present}
          onClick={() => {}}
          color="#4A90D9"
        />
        <Action
          label="Export Report"
          desc="Save repair report to Phoenix Key"
          disabled={!key?.present}
          onClick={() => {}}
          color="#8A929E"
        />
      </div>

      {/* Footer */}
      <div style={s.footer}>
        <span>Phoenix OS v0.1.0-alpha</span>
        <span>·</span>
        <span>VID:1209 PID:B00F</span>
      </div>
    </div>
  );
}

function MetaRow({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ display: "flex", gap: "8px", fontSize: "12px", padding: "2px 0" }}>
      <span style={{ color: "#4A515C", width: "50px" }}>{label}</span>
      <span style={{ color: "#E8EAF0", fontFamily: "monospace" }}>{value}</span>
    </div>
  );
}

function Action({ label, desc, disabled, onClick, color }: {
  label: string; desc: string; disabled: boolean; onClick: () => void; color: string;
}) {
  const [hovered, setHovered] = useState(false);
  return (
    <button
      style={{
        ...s.action,
        opacity:     disabled ? 0.35 : 1,
        borderColor: hovered && !disabled ? color : "#2A2F38",
      }}
      disabled={disabled}
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <div style={{ width: "3px", height: "36px", backgroundColor: color, borderRadius: "2px", flexShrink: 0 }} />
      <div>
        <div style={{ color: "#E8EAF0", fontSize: "13px", fontWeight: 600 }}>{label}</div>
        <div style={{ color: "#8A929E", fontSize: "11px", marginTop: "2px" }}>{desc}</div>
      </div>
    </button>
  );
}

const s: Record<string, React.CSSProperties> = {
  root:    { height: "100vh", backgroundColor: "#0D0F12", display: "flex", flexDirection: "column", padding: "24px", fontFamily: "'IBM Plex Mono', monospace", gap: "16px" },
  header:  { display: "flex", alignItems: "center", gap: "14px", paddingBottom: "16px", borderBottom: "1px solid #2A2F38" },
  flame:   { fontSize: "32px" },
  title:   { color: "#F58C1F", fontSize: "22px", fontWeight: "700", fontFamily: "'Rajdhani', sans-serif", letterSpacing: "0.15em", lineHeight: 1 },
  sub:     { color: "#4A515C", fontSize: "11px", letterSpacing: "0.08em", marginTop: "3px" },
  keyCard: { backgroundColor: "#161A1F", border: "2px solid", borderRadius: "8px", padding: "16px 18px", display: "flex", alignItems: "flex-start", gap: "14px", transition: "border-color 0.3s" },
  keyDot:  (present: boolean) => ({
    width: "12px", height: "12px", borderRadius: "50%", marginTop: "4px", flexShrink: 0,
    backgroundColor: present ? "#F58C1F" : "#2A2F38",
    boxShadow: present ? "0 0 8px #F58C1F88" : "none",
  } as React.CSSProperties),
  keyInfo: { flex: 1 },
  keyMeta: { marginTop: "10px", display: "flex", flexDirection: "column", gap: "2px" },
  actions: { display: "flex", flexDirection: "column", gap: "8px", flex: 1 },
  action:  { display: "flex", alignItems: "center", gap: "14px", backgroundColor: "#161A1F", border: "1px solid", borderRadius: "8px", padding: "12px 16px", cursor: "pointer", textAlign: "left", transition: "border-color 0.15s, background 0.15s" },
  footer:  { display: "flex", gap: "8px", color: "#4A515C", fontSize: "11px", paddingTop: "12px", borderTop: "1px solid #2A2F38" },
};
