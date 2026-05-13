import { useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import { AlertTriangle, Shield, XCircle } from "lucide-react";

interface Props {
  device:           string;
  operationLabel:   string;
  operationDesc:    string;
  onConfirmed:      () => void;
  onCancelled:      () => void;
}

interface DeviceDetails {
  path:          string;
  model:         string;
  serial:        string;
  size_human:    string;
  bus_type:      string;
  is_live_device: boolean;
}

/**
 * ConfirmGate — the Phoenix OS destructive-operation confirmation UI.
 *
 * Implements Principle 2 of the Phoenix disk safety model:
 *   - Shows full device details (model, serial, size, path)
 *   - User must TYPE the device path exactly to confirm
 *   - No confirmation by clicking alone
 *
 * See docs/security-model.md — Principle 2: Confirmation Gates
 */
export default function ConfirmGate({ device, operationLabel, operationDesc, onConfirmed, onCancelled }: Props) {
  const [typed,   setTyped]   = useState("");
  const [details, setDetails] = useState<DeviceDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState<string | null>(null);

  // Load device details on mount
  useState(() => {
    invoke<DeviceDetails>("get_device_details", { devicePath: device })
      .then(d => { setDetails(d); setLoading(false); })
      .catch(e => { setError(String(e)); setLoading(false); });
  });

  const isMatch = typed.trim() === device;

  const handleConfirm = async () => {
    if (!isMatch) return;
    try {
      await invoke("confirm_destructive_operation", {
        request: {
          typed_path:            typed.trim(),
          target_path:           device,
          operation_description: operationLabel,
        },
      });
      onConfirmed();
    } catch (e) {
      setError(String(e));
    }
  };

  return (
    <div style={s.overlay}>
      <div style={s.modal}>
        {/* Header */}
        <div style={s.header}>
          <AlertTriangle size={22} color="#D94215" />
          <div>
            <div style={s.title}>Confirm Destructive Operation</div>
            <div style={s.op}>{operationLabel}</div>
          </div>
        </div>

        {/* Operation description */}
        <div style={s.desc}>{operationDesc}</div>

        {/* Device info panel */}
        <div style={s.devicePanel}>
          <div style={s.panelLabel}>TARGET DEVICE</div>

          {loading && <div style={s.loading}>Loading device details…</div>}

          {error && (
            <div style={s.errorRow}>
              <XCircle size={13} color="#E03A3A" />
              <span style={{ color: "#E03A3A", fontSize: "12px" }}>
                Could not load device details: {error}
              </span>
            </div>
          )}

          {details && (
            <table style={s.table}>
              <tbody>
                <InfoRow label="Path"   value={details.path}      mono highlight />
                <InfoRow label="Model"  value={details.model}     mono />
                <InfoRow label="Serial" value={details.serial}    mono />
                <InfoRow label="Size"   value={details.size_human}      />
                <InfoRow label="Bus"    value={details.bus_type.toUpperCase()} />
              </tbody>
            </table>
          )}

          {details?.is_live_device && (
            <div style={s.liveWarning}>
              <Shield size={13} color="#E03A3A" />
              <span style={{ color: "#E03A3A" }}>
                This appears to be the Phoenix OS boot device. Modifying it may make it unbootable.
              </span>
            </div>
          )}
        </div>

        {/* Type-to-confirm */}
        <div style={s.confirmField}>
          <label style={s.confirmLabel}>
            Type <code style={s.code}>{device}</code> to confirm:
          </label>
          <input
            style={{ ...s.input, borderColor: typed ? (isMatch ? "#3DB882" : "#E03A3A") : "#2A2F38" }}
            value={typed}
            onChange={e => setTyped(e.target.value)}
            placeholder={device}
            spellCheck={false}
            autoFocus
            onKeyDown={e => e.key === "Enter" && isMatch && handleConfirm()}
          />
          {typed && !isMatch && (
            <div style={s.mismatch}>
              <XCircle size={12} color="#E03A3A" />
              Path does not match. Type exactly: {device}
            </div>
          )}
        </div>

        {/* Actions */}
        <div style={s.actions}>
          <button style={s.cancelBtn} onClick={onCancelled}>
            Cancel
          </button>
          <button
            style={{ ...s.confirmBtn, opacity: isMatch ? 1 : 0.35 }}
            disabled={!isMatch}
            onClick={handleConfirm}
          >
            <AlertTriangle size={14} />
            Confirm — Proceed with {operationLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

function InfoRow({ label, value, mono, highlight }: { label: string; value: string; mono?: boolean; highlight?: boolean }) {
  return (
    <tr>
      <td style={s.tdLabel}>{label}</td>
      <td style={{
        ...s.tdValue,
        fontFamily: mono ? "'IBM Plex Mono', monospace" : "inherit",
        color: highlight ? "#F58C1F" : "#E8EAF0",
        fontWeight: highlight ? 600 : 400,
      }}>{value}</td>
    </tr>
  );
}

const s: Record<string, React.CSSProperties> = {
  overlay:      { backgroundColor: "#161A1F", border: "1px solid #D94215", borderRadius: "8px", padding: "24px", maxWidth: "560px", margin: "0 auto" },
  modal:        {},
  header:       { display: "flex", alignItems: "flex-start", gap: "14px", marginBottom: "16px" },
  title:        { color: "#E8EAF0", fontSize: "16px", fontWeight: "700", fontFamily: "'Rajdhani', sans-serif" },
  op:           { color: "#D94215", fontSize: "12px", marginTop: "3px" },
  desc:         { color: "#8A929E", fontSize: "12px", lineHeight: "1.6", marginBottom: "18px", padding: "12px", backgroundColor: "#1E2329", borderRadius: "6px" },
  devicePanel:  { backgroundColor: "#0D0F12", border: "1px solid #2A2F38", borderRadius: "8px", padding: "14px 16px", marginBottom: "18px" },
  panelLabel:   { color: "#4A515C", fontSize: "10px", fontWeight: "700", letterSpacing: "0.12em", textTransform: "uppercase", marginBottom: "10px" },
  loading:      { color: "#8A929E", fontSize: "12px" },
  errorRow:     { display: "flex", alignItems: "center", gap: "8px" },
  table:        { width: "100%", borderCollapse: "collapse" },
  tdLabel:      { color: "#8A929E", fontSize: "11px", padding: "4px 0", width: "60px", textTransform: "uppercase", letterSpacing: "0.06em" },
  tdValue:      { fontSize: "12px", padding: "4px 0" },
  liveWarning:  { display: "flex", alignItems: "center", gap: "8px", backgroundColor: "#1A0A0A", border: "1px solid #E03A3A", borderRadius: "6px", padding: "8px 10px", marginTop: "12px", fontSize: "12px", lineHeight: "1.5" },
  confirmField: { marginBottom: "18px" },
  confirmLabel: { display: "block", color: "#8A929E", fontSize: "12px", marginBottom: "8px", lineHeight: "1.6" },
  code:         { backgroundColor: "#1E2329", padding: "2px 6px", borderRadius: "3px", color: "#F58C1F", fontFamily: "'IBM Plex Mono', monospace", fontSize: "12px" },
  input:        { width: "100%", backgroundColor: "#0D0F12", border: "1px solid", borderRadius: "6px", padding: "10px 12px", color: "#E8EAF0", fontSize: "13px", fontFamily: "'IBM Plex Mono', monospace", outline: "none" },
  mismatch:     { display: "flex", alignItems: "center", gap: "6px", color: "#E03A3A", fontSize: "11px", marginTop: "6px" },
  actions:      { display: "flex", justifyContent: "flex-end", gap: "10px" },
  cancelBtn:    { backgroundColor: "#1E2329", border: "1px solid #2A2F38", borderRadius: "6px", padding: "9px 18px", color: "#8A929E", fontSize: "13px", cursor: "pointer" },
  confirmBtn:   { display: "flex", alignItems: "center", gap: "8px", backgroundColor: "#D94215", border: "none", borderRadius: "6px", padding: "9px 18px", color: "#E8EAF0", fontSize: "13px", fontWeight: "600", cursor: "pointer", transition: "opacity 0.15s" },
};
