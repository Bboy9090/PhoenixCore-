import { useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import { RotateCcw, HardDrive, FolderOpen, Play, Info, AlertTriangle } from "lucide-react";

interface DdrescueOptions {
  source_device: string;
  output_image:  string;
  mapfile:       string;
  retry_passes:  number;
  direct_io:     boolean;
}

export default function DataRescueView() {
  const [tool, setTool] = useState<"ddrescue" | "photorec">("ddrescue");

  // ddrescue state
  const [source,      setSource]      = useState("");
  const [outputImage, setOutputImage] = useState("");
  const [mapfile,     setMapfile]     = useState("");
  const [retryPasses, setRetryPasses] = useState(3);
  const [directIo,    setDirectIo]    = useState(true);
  const [result,      setResult]      = useState<string | null>(null);
  const [running,     setRunning]     = useState(false);

  // photorec state
  const [prSource, setPrSource] = useState("");
  const [prOutput, setPrOutput] = useState("");

  const runDdrescue = async () => {
    if (!source || !outputImage || !mapfile) return;
    setRunning(true);
    try {
      const opts: DdrescueOptions = {
        source_device: source, output_image: outputImage,
        mapfile, retry_passes: retryPasses, direct_io: directIo,
      };
      const msg = await invoke<string>("start_ddrescue", { opts });
      setResult(msg);
    } catch (e) {
      setResult(`Error: ${e}`);
    } finally {
      setRunning(false);
    }
  };

  const runPhotorec = async () => {
    if (!prSource || !prOutput) return;
    setRunning(true);
    try {
      const msg = await invoke<string>("run_photorec", {
        opts: { source_device: prSource, output_dir: prOutput, file_types: [] }
      });
      setResult(msg);
    } catch (e) {
      setResult(`Error: ${e}`);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div style={s.page}>
      <div style={s.header}>
        <RotateCcw size={18} color="#3DB882" />
        <div>
          <h1 style={s.title}>Data Rescue</h1>
          <p style={s.sub}>Recover data from failing drives and deleted files via signature scanning.</p>
        </div>
      </div>

      {/* Tool tabs */}
      <div style={s.tabs}>
        {(["ddrescue", "photorec"] as const).map(t => (
          <button
            key={t}
            style={{ ...s.tab, ...(tool === t ? s.tabActive : {}) }}
            onClick={() => setTool(t)}
          >
            {t === "ddrescue" ? "GNU ddrescue — Disk Imaging" : "PhotoRec — File Recovery"}
          </button>
        ))}
      </div>

      {/* ddrescue panel */}
      {tool === "ddrescue" && (
        <div style={s.card}>
          <div style={s.infoBox}>
            <Info size={13} color="#4A90D9" />
            <span>
              ddrescue reads the <strong>source device</strong> and writes a byte-for-byte image to a <strong>file</strong>.
              It skips bad sectors and retries, maximising recovered data. The mapfile enables resuming interrupted rescues.
            </span>
          </div>

          <Field label="Source device (failing disk)" placeholder="/dev/sdb"
            value={source} onChange={setSource}
            hint="The damaged disk or partition to read from." />

          <Field label="Output image file" placeholder="/mnt/usb/rescue.img"
            value={outputImage} onChange={setOutputImage}
            hint="Must be on a DIFFERENT device than the source. Needs space equal to source size." />

          <Field label="Mapfile path" placeholder="/mnt/usb/rescue.map"
            value={mapfile} onChange={setMapfile}
            hint="Saves progress for resumable sessions. Use the same file if resuming." />

          <div style={s.row}>
            <div style={s.halfField}>
              <label style={s.label}>Retry passes</label>
              <select style={s.select} value={retryPasses} onChange={e => setRetryPasses(+e.target.value)}>
                {[0,1,3,5,10].map(n => <option key={n} value={n}>{n === 0 ? "0 (skip bad sectors)" : n}</option>)}
              </select>
            </div>
            <div style={s.halfField}>
              <label style={s.label}>Direct I/O</label>
              <div style={s.toggle} onClick={() => setDirectIo(v => !v)}>
                <div style={{ ...s.toggleTrack, backgroundColor: directIo ? "#3DB882" : "#2A2F38" }}>
                  <div style={{ ...s.toggleThumb, transform: directIo ? "translateX(18px)" : "translateX(2px)" }} />
                </div>
                <span style={{ color: "#8A929E", fontSize: "12px" }}>
                  {directIo ? "Enabled (bypass OS cache — recommended for failing drives)" : "Disabled"}
                </span>
              </div>
            </div>
          </div>

          <button
            style={{ ...s.btn, backgroundColor: "#3DB882", opacity: (source && outputImage && mapfile && !running) ? 1 : 0.4 }}
            disabled={!source || !outputImage || !mapfile || running}
            onClick={runDdrescue}
          >
            <Play size={14} />
            {running ? "Starting ddrescue…" : "Start Rescue"}
          </button>

          {result && <div style={s.resultBox}>{result}</div>}
        </div>
      )}

      {/* photorec panel */}
      {tool === "photorec" && (
        <div style={s.card}>
          <div style={s.infoBox}>
            <Info size={13} color="#4A90D9" />
            <span>
              PhotoRec scans disk sectors for file signatures (JPEG, PDF, DOCX, MP4, and 500+ more)
              and recovers them regardless of the filesystem state. It does not recover filenames.
            </span>
          </div>

          <div style={s.warningBox}>
            <AlertTriangle size={13} color="#F5C842" />
            <span>
              PhotoRec opens in a terminal TUI. Follow the on-screen prompts to select the partition
              and output directory. Recovered files are numbered, not named.
            </span>
          </div>

          <Field label="Source device or partition" placeholder="/dev/sdb  or  /dev/sdb1"
            value={prSource} onChange={setPrSource}
            hint="Scan the whole disk (/dev/sdb) or a specific partition (/dev/sdb1)." />

          <Field label="Output directory" placeholder="/mnt/usb/recovered"
            value={prOutput} onChange={setPrOutput}
            hint="Recovered files are written here. Must be on a different device than the source." />

          <button
            style={{ ...s.btn, backgroundColor: "#3DB882", opacity: (prSource && prOutput && !running) ? 1 : 0.4 }}
            disabled={!prSource || !prOutput || running}
            onClick={runPhotorec}
          >
            <Play size={14} />
            Launch PhotoRec
          </button>

          {result && <div style={s.resultBox}>{result}</div>}
        </div>
      )}
    </div>
  );
}

function Field({ label, placeholder, value, onChange, hint }: {
  label: string; placeholder: string; value: string;
  onChange: (v: string) => void; hint?: string;
}) {
  return (
    <div style={{ marginBottom: "16px" }}>
      <label style={s.label}>{label}</label>
      <input
        style={s.input}
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        spellCheck={false}
      />
      {hint && <span style={s.hint}>{hint}</span>}
    </div>
  );
}

const s: Record<string, React.CSSProperties> = {
  page:        { padding: "28px 32px", height: "100%", overflowY: "auto" },
  header:      { display: "flex", alignItems: "flex-start", gap: "12px", marginBottom: "20px", paddingBottom: "16px", borderBottom: "1px solid #2A2F38" },
  title:       { color: "#E8EAF0", fontSize: "20px", fontWeight: "700", fontFamily: "'Rajdhani', sans-serif" },
  sub:         { color: "#8A929E", fontSize: "12px", marginTop: "4px" },
  tabs:        { display: "flex", gap: "4px", marginBottom: "16px" },
  tab:         { backgroundColor: "#161A1F", border: "1px solid #2A2F38", borderRadius: "6px", padding: "8px 16px", color: "#8A929E", fontSize: "12px", cursor: "pointer" },
  tabActive:   { backgroundColor: "#1E2329", borderColor: "#3DB882", color: "#E8EAF0" },
  card:        { backgroundColor: "#161A1F", border: "1px solid #2A2F38", borderRadius: "8px", padding: "20px" },
  infoBox:     { display: "flex", alignItems: "flex-start", gap: "8px", backgroundColor: "#0A1020", border: "1px solid #4A90D9", borderRadius: "6px", padding: "10px 12px", marginBottom: "18px", color: "#8A929E", fontSize: "12px", lineHeight: "1.6" },
  warningBox:  { display: "flex", alignItems: "flex-start", gap: "8px", backgroundColor: "#1A180A", border: "1px solid #F5C842", borderRadius: "6px", padding: "10px 12px", marginBottom: "18px", color: "#8A929E", fontSize: "12px", lineHeight: "1.6" },
  label:       { display: "block", color: "#8A929E", fontSize: "11px", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: "6px" },
  input:       { width: "100%", backgroundColor: "#1E2329", border: "1px solid #2A2F38", borderRadius: "6px", padding: "9px 12px", color: "#E8EAF0", fontSize: "13px", fontFamily: "'IBM Plex Mono', monospace", outline: "none" },
  hint:        { display: "block", color: "#4A515C", fontSize: "11px", marginTop: "5px" },
  row:         { display: "flex", gap: "16px", marginBottom: "16px" },
  halfField:   { flex: 1 },
  select:      { width: "100%", backgroundColor: "#1E2329", border: "1px solid #2A2F38", borderRadius: "6px", padding: "9px 12px", color: "#E8EAF0", fontSize: "13px", outline: "none" },
  toggle:      { display: "flex", alignItems: "center", gap: "10px", cursor: "pointer", marginTop: "2px" },
  toggleTrack: { width: "38px", height: "22px", borderRadius: "11px", position: "relative", transition: "background 0.2s", flexShrink: 0 },
  toggleThumb: { position: "absolute", top: "3px", width: "16px", height: "16px", backgroundColor: "#E8EAF0", borderRadius: "50%", transition: "transform 0.2s" },
  btn:         { display: "flex", alignItems: "center", gap: "8px", border: "none", borderRadius: "6px", padding: "10px 18px", color: "#E8EAF0", fontSize: "13px", fontWeight: "600", cursor: "pointer", marginTop: "4px" },
  resultBox:   { marginTop: "16px", backgroundColor: "#0D0F12", border: "1px solid #2A2F38", borderRadius: "6px", padding: "12px 14px", color: "#E8EAF0", fontSize: "12px", fontFamily: "'IBM Plex Mono', monospace", lineHeight: "1.7" },
};
