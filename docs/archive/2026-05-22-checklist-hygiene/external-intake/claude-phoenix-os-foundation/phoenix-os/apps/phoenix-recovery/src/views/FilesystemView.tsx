import { useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import { HardDrive, Play, AlertTriangle, CheckCircle, XCircle, Info } from "lucide-react";
import ConfirmGate from "../components/ConfirmGate";

interface FsckOptions {
  device:      string;
  dry_run:     boolean;
  force:       boolean;
  auto_repair: boolean;
}

interface FsckResult {
  device:       string;
  exit_code:    number;
  output:       string;
  errors_found: boolean;
  errors_fixed: boolean;
  summary:      string;
}

type Step = "select" | "confirm" | "running" | "done";

export default function FilesystemView() {
  const [step,      setStep]      = useState<Step>("select");
  const [device,    setDevice]    = useState("");
  const [dryRun,    setDryRun]    = useState(true);
  const [force,     setForce]     = useState(false);
  const [autoRepair,setAutoRepair]= useState(false);
  const [result,    setResult]    = useState<FsckResult | null>(null);
  const [running,   setRunning]   = useState(false);

  const handleConfirmed = async () => {
    setStep("running");
    setRunning(true);
    try {
      const opts: FsckOptions = { device, dry_run: dryRun, force, auto_repair: autoRepair };
      const res = await invoke<FsckResult>("run_fsck", { opts });
      setResult(res);
      setStep("done");
    } catch (e) {
      setResult({ device, exit_code: -1, output: String(e), errors_found: true, errors_fixed: false, summary: "Failed to run fsck." });
      setStep("done");
    } finally {
      setRunning(false);
    }
  };

  return (
    <div style={s.page}>
      <div style={s.header}>
        <HardDrive size={18} color="#4A90D9" />
        <div>
          <h1 style={s.title}>Filesystem Repair</h1>
          <p style={s.sub}>Check and repair ext2/3/4, XFS, Btrfs, NTFS, and FAT filesystems.</p>
        </div>
      </div>

      {/* Step: Select */}
      {step === "select" && (
        <div style={s.card}>
          <div style={s.cardTitle}>Target Partition</div>

          <div style={s.field}>
            <label style={s.label}>Device path</label>
            <input
              style={s.input}
              value={device}
              onChange={e => setDevice(e.target.value)}
              placeholder="/dev/sdb1"
              spellCheck={false}
            />
            <span style={s.hint}>Enter the partition to check (e.g. /dev/sdb1). The filesystem must be unmounted.</span>
          </div>

          <div style={s.field}>
            <div style={s.cardTitle}>Options</div>
            <ToggleRow
              label="Check only (no repairs)"
              desc="Recommended first step — reports errors without changing anything."
              checked={dryRun}
              onChange={v => { setDryRun(v); if (v) setAutoRepair(false); }}
            />
            <ToggleRow
              label="Force check"
              desc="Run fsck even if the filesystem appears clean."
              checked={force}
              onChange={setForce}
            />
            <ToggleRow
              label="Auto-repair (fsck -y)"
              desc="Automatically fix all errors without prompting. Destructive — requires confirmation."
              checked={autoRepair}
              onChange={v => { setAutoRepair(v); if (v) setDryRun(false); }}
              danger
            />
          </div>

          <div style={s.warningBox}>
            <AlertTriangle size={13} color="#F5C842" />
            <span>The target filesystem must be <strong>unmounted</strong> before running fsck. Running on a mounted filesystem causes corruption.</span>
          </div>

          <button
            style={{ ...s.btn, opacity: device.trim() ? 1 : 0.4 }}
            disabled={!device.trim()}
            onClick={() => setStep(autoRepair ? "confirm" : "running")}
          >
            <Play size={14} />
            {dryRun ? "Run Check" : "Run Repair"}
          </button>

          {/* Skip confirm gate for read-only dry run */}
          {step === "running" && !autoRepair && (
            (handleConfirmed(), undefined)
          )}
        </div>
      )}

      {/* Step: Confirm (auto-repair only) */}
      {step === "confirm" && (
        <ConfirmGate
          device={device}
          operationLabel="Filesystem Auto-Repair (fsck -y)"
          operationDesc="This will automatically fix all filesystem errors on the selected partition. Data may be modified or deleted during repair."
          onConfirmed={handleConfirmed}
          onCancelled={() => setStep("select")}
        />
      )}

      {/* Step: Running */}
      {step === "running" && (
        <div style={s.card}>
          <div style={{ ...s.cardTitle, color: "#4A90D9" }}>Running fsck on {device}…</div>
          <div style={s.spinner}>
            <div style={s.spinnerDot} />
            <span style={{ color: "#8A929E" }}>This may take several minutes on large partitions.</span>
          </div>
        </div>
      )}

      {/* Step: Done */}
      {step === "done" && result && (
        <div>
          <div style={{ ...s.card, borderColor: result.errors_found && !result.errors_fixed ? "#E03A3A" : result.errors_fixed ? "#F5C842" : "#3DB882" }}>
            <div style={s.resultHeader}>
              {result.errors_found && !result.errors_fixed
                ? <XCircle size={20} color="#E03A3A" />
                : result.errors_fixed
                ? <AlertTriangle size={20} color="#F5C842" />
                : <CheckCircle size={20} color="#3DB882" />
              }
              <div>
                <div style={s.cardTitle}>{result.summary}</div>
                <div style={{ color: "#8A929E", fontSize: "12px" }}>
                  Exit code: {result.exit_code} · {result.device}
                </div>
              </div>
            </div>
          </div>

          <div style={s.outputCard}>
            <div style={s.outputLabel}>fsck output</div>
            <pre style={s.output}>{result.output || "(no output)"}</pre>
          </div>

          <button style={s.btnSecondary} onClick={() => { setStep("select"); setResult(null); }}>
            Run Another Check
          </button>
        </div>
      )}
    </div>
  );
}

function ToggleRow({ label, desc, checked, onChange, danger }: {
  label: string; desc: string; checked: boolean;
  onChange: (v: boolean) => void; danger?: boolean;
}) {
  return (
    <div style={t.row} onClick={() => onChange(!checked)}>
      <div style={t.check(checked, danger)}>
        {checked && <div style={t.checkInner} />}
      </div>
      <div>
        <div style={{ color: danger ? "#E03A3A" : "#E8EAF0", fontSize: "13px", fontWeight: 500 }}>{label}</div>
        <div style={{ color: "#8A929E", fontSize: "11px", marginTop: "2px" }}>{desc}</div>
      </div>
    </div>
  );
}

const s: Record<string, React.CSSProperties> = {
  page:        { padding: "28px 32px", height: "100%", overflowY: "auto" },
  header:      { display: "flex", alignItems: "flex-start", gap: "12px", marginBottom: "24px", paddingBottom: "16px", borderBottom: "1px solid #2A2F38" },
  title:       { color: "#E8EAF0", fontSize: "20px", fontWeight: "700", fontFamily: "'Rajdhani', sans-serif", letterSpacing: "0.04em" },
  sub:         { color: "#8A929E", fontSize: "12px", marginTop: "4px" },
  card:        { backgroundColor: "#161A1F", border: "1px solid #2A2F38", borderRadius: "8px", padding: "20px", marginBottom: "16px" },
  cardTitle:   { color: "#E8EAF0", fontSize: "13px", fontWeight: "600", marginBottom: "14px" },
  field:       { marginBottom: "20px" },
  label:       { display: "block", color: "#8A929E", fontSize: "11px", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: "6px" },
  input:       { width: "100%", backgroundColor: "#1E2329", border: "1px solid #2A2F38", borderRadius: "6px", padding: "9px 12px", color: "#E8EAF0", fontSize: "13px", fontFamily: "'IBM Plex Mono', monospace", outline: "none" },
  hint:        { display: "block", color: "#4A515C", fontSize: "11px", marginTop: "5px" },
  warningBox:  { display: "flex", alignItems: "flex-start", gap: "8px", backgroundColor: "#1A180A", border: "1px solid #F5C842", borderRadius: "6px", padding: "10px 12px", marginBottom: "16px", color: "#8A929E", fontSize: "12px", lineHeight: "1.5" },
  btn:         { display: "flex", alignItems: "center", gap: "8px", backgroundColor: "#4A90D9", border: "none", borderRadius: "6px", padding: "10px 18px", color: "#E8EAF0", fontSize: "13px", fontWeight: "600", cursor: "pointer" },
  btnSecondary:{ display: "flex", alignItems: "center", gap: "8px", backgroundColor: "#1E2329", border: "1px solid #2A2F38", borderRadius: "6px", padding: "9px 16px", color: "#E8EAF0", fontSize: "13px", cursor: "pointer", marginTop: "4px" },
  spinner:     { display: "flex", alignItems: "center", gap: "12px", padding: "20px 0" },
  spinnerDot:  { width: "10px", height: "10px", borderRadius: "50%", backgroundColor: "#4A90D9", animation: "pulse 1.2s infinite" },
  resultHeader:{ display: "flex", alignItems: "center", gap: "12px" },
  outputCard:  { backgroundColor: "#0D0F12", border: "1px solid #2A2F38", borderRadius: "8px", padding: "16px", marginBottom: "16px" },
  outputLabel: { color: "#4A515C", fontSize: "10px", fontWeight: "700", letterSpacing: "0.12em", textTransform: "uppercase", marginBottom: "10px" },
  output:      { color: "#E8EAF0", fontSize: "11px", fontFamily: "'IBM Plex Mono', monospace", whiteSpace: "pre-wrap", wordBreak: "break-all", maxHeight: "320px", overflowY: "auto", lineHeight: "1.7" },
};

const t: Record<string, any> = {
  row:   { display: "flex", alignItems: "flex-start", gap: "12px", padding: "10px 0", cursor: "pointer", borderBottom: "1px solid #1E2329" } as React.CSSProperties,
  check: (checked: boolean, danger?: boolean) => ({
    width: "18px", height: "18px", minWidth: "18px", borderRadius: "4px",
    border: `1px solid ${checked ? (danger ? "#E03A3A" : "#F58C1F") : "#2A2F38"}`,
    backgroundColor: checked ? (danger ? "#E03A3A20" : "#F58C1F20") : "transparent",
    display: "flex", alignItems: "center", justifyContent: "center", marginTop: "2px",
  } as React.CSSProperties),
  checkInner: { width: "8px", height: "8px", borderRadius: "2px", backgroundColor: "#F58C1F" } as React.CSSProperties,
};
