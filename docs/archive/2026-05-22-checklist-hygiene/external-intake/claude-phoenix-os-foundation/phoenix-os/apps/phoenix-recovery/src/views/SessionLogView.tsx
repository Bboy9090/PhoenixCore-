import { useEffect, useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import { FileText, Download, RefreshCw, CheckCircle, AlertTriangle, XCircle, Info } from "lucide-react";

interface LogEntry {
  timestamp_unix: number;
  level:          "Info" | "Success" | "Warning" | "Error";
  category:       string;
  message:        string;
  detail:         string | null;
}

const LEVEL_CONFIG = {
  Info:    { color: "#4A90D9",  icon: Info          },
  Success: { color: "#3DB882",  icon: CheckCircle   },
  Warning: { color: "#F5C842",  icon: AlertTriangle },
  Error:   { color: "#E03A3A",  icon: XCircle       },
};

export default function SessionLogView() {
  const [entries,  setEntries]  = useState<LogEntry[]>([]);
  const [rawLog,   setRawLog]   = useState("");
  const [viewMode, setViewMode] = useState<"structured" | "raw">("structured");
  const [loading,  setLoading]  = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const [e, r] = await Promise.all([
        invoke<LogEntry[]>("get_session_log"),
        invoke<string>("export_session_log"),
      ]);
      setEntries(e);
      setRawLog(r);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const saveLog = () => {
    // In a real implementation, use the Tauri file save dialog
    // For now, copy to clipboard
    navigator.clipboard.writeText(rawLog).then(() => {
      alert("Session log copied to clipboard.");
    });
  };

  return (
    <div style={s.page}>
      <div style={s.header}>
        <FileText size={18} color="#8A929E" />
        <div>
          <h1 style={s.title}>Session Log</h1>
          <p style={s.sub}>All operations performed in this recovery session.</p>
        </div>
        <div style={s.actions}>
          <button style={s.btn} onClick={load} disabled={loading}>
            <RefreshCw size={13} />
            Refresh
          </button>
          <button style={{ ...s.btn, backgroundColor: "#1E2329" }} onClick={saveLog}>
            <Download size={13} />
            Copy Log
          </button>
        </div>
      </div>

      {/* View mode toggle */}
      <div style={s.toggleRow}>
        {(["structured", "raw"] as const).map(m => (
          <button
            key={m}
            style={{ ...s.toggleBtn, ...(viewMode === m ? s.toggleBtnActive : {}) }}
            onClick={() => setViewMode(m)}
          >
            {m === "structured" ? "Structured" : "Raw Text"}
          </button>
        ))}
        <span style={s.count}>{entries.length} entries</span>
      </div>

      {/* Structured view */}
      {viewMode === "structured" && (
        <div style={s.logList}>
          {entries.length === 0 && !loading && (
            <div style={s.empty}>
              No log entries yet. Perform recovery operations and they will appear here.
            </div>
          )}
          {entries.map((entry, i) => {
            const { color, icon: Icon } = LEVEL_CONFIG[entry.level];
            return (
              <div key={i} style={s.entry}>
                <div style={s.entryMeta}>
                  <Icon size={13} color={color} style={{ flexShrink: 0 }} />
                  <span style={{ ...s.level, color }}>{entry.level}</span>
                  <span style={s.category}>[{entry.category}]</span>
                  <span style={s.ts}>{new Date(entry.timestamp_unix * 1000).toLocaleTimeString()}</span>
                </div>
                <div style={s.message}>{entry.message}</div>
                {entry.detail && <div style={s.detail}>{entry.detail}</div>}
              </div>
            );
          })}
        </div>
      )}

      {/* Raw view */}
      {viewMode === "raw" && (
        <pre style={s.raw}>
          {rawLog || "Session log is empty."}
        </pre>
      )}
    </div>
  );
}

const s: Record<string, React.CSSProperties> = {
  page:         { padding: "28px 32px", height: "100%", overflowY: "auto" },
  header:       { display: "flex", alignItems: "flex-start", gap: "12px", marginBottom: "20px", paddingBottom: "16px", borderBottom: "1px solid #2A2F38" },
  title:        { color: "#E8EAF0", fontSize: "20px", fontWeight: "700", fontFamily: "'Rajdhani', sans-serif" },
  sub:          { color: "#8A929E", fontSize: "12px", marginTop: "4px" },
  actions:      { display: "flex", gap: "8px", marginLeft: "auto" },
  btn:          { display: "flex", alignItems: "center", gap: "6px", backgroundColor: "#1E2329", border: "1px solid #2A2F38", borderRadius: "6px", padding: "7px 12px", color: "#E8EAF0", fontSize: "12px", cursor: "pointer" },
  toggleRow:    { display: "flex", alignItems: "center", gap: "6px", marginBottom: "14px" },
  toggleBtn:    { backgroundColor: "#161A1F", border: "1px solid #2A2F38", borderRadius: "5px", padding: "6px 12px", color: "#8A929E", fontSize: "12px", cursor: "pointer" },
  toggleBtnActive:{ backgroundColor: "#1E2329", borderColor: "#8A929E", color: "#E8EAF0" },
  count:        { color: "#4A515C", fontSize: "11px", marginLeft: "auto" },
  logList:      { display: "flex", flexDirection: "column", gap: "4px" },
  empty:        { color: "#4A515C", fontSize: "13px", padding: "32px", textAlign: "center", backgroundColor: "#161A1F", borderRadius: "8px", border: "1px dashed #2A2F38" },
  entry:        { backgroundColor: "#161A1F", border: "1px solid #2A2F38", borderRadius: "6px", padding: "10px 14px" },
  entryMeta:    { display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" },
  level:        { fontSize: "11px", fontWeight: "700", width: "52px" },
  category:     { color: "#4A515C", fontSize: "11px", fontFamily: "'IBM Plex Mono', monospace" },
  ts:           { color: "#4A515C", fontSize: "11px", marginLeft: "auto", fontFamily: "'IBM Plex Mono', monospace" },
  message:      { color: "#E8EAF0", fontSize: "12px" },
  detail:       { color: "#8A929E", fontSize: "11px", marginTop: "4px", fontFamily: "'IBM Plex Mono', monospace", paddingLeft: "8px", borderLeft: "2px solid #2A2F38" },
  raw:          { backgroundColor: "#0D0F12", border: "1px solid #2A2F38", borderRadius: "8px", padding: "16px", color: "#E8EAF0", fontSize: "11px", fontFamily: "'IBM Plex Mono', monospace", whiteSpace: "pre-wrap", lineHeight: "1.7", overflowY: "auto", maxHeight: "calc(100vh - 220px)" },
};
