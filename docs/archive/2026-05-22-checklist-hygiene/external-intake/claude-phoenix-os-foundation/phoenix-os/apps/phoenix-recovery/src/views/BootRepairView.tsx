import { useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import { Cpu, Play, CheckCircle, XCircle, AlertTriangle, ChevronRight } from "lucide-react";
import ConfirmGate from "../components/ConfirmGate";

interface RepairResult { success: boolean; log: string; next_steps: string[]; }
type Step = "select" | "confirm" | "running" | "done";
type Firmware = "Bios" | "Uefi";

export default function BootRepairView() {
  const [mode,      setMode]      = useState<"grub" | "mbr">("grub");
  const [disk,      setDisk]      = useState("");
  const [chrootRoot,setChrootRoot]= useState("");
  const [firmware,  setFirmware]  = useState<Firmware>("Uefi");
  const [efiMount,  setEfiMount]  = useState("/boot/efi");
  const [step,      setStep]      = useState<Step>("select");
  const [result,    setResult]    = useState<RepairResult | null>(null);

  const handleConfirmed = async () => {
    setStep("running");
    try {
      let res: RepairResult;
      if (mode === "grub") {
        res = await invoke<RepairResult>("repair_grub", {
          opts: {
            target_disk:   disk,
            chroot_root:   chrootRoot,
            firmware_mode: firmware,
            efi_mount:     firmware === "Uefi" ? efiMount : null,
          }
        });
      } else {
        res = await invoke<RepairResult>("repair_mbr", { targetDisk: disk });
      }
      setResult(res);
      setStep("done");
    } catch (e) {
      setResult({ success: false, log: String(e), next_steps: ["Review the error and retry."] });
      setStep("done");
    }
  };

  return (
    <div style={s.page}>
      <div style={s.header}>
        <Cpu size={18} color="#F58C1F" />
        <div>
          <h1 style={s.title}>Boot Repair</h1>
          <p style={s.sub}>Reinstall GRUB or repair the MBR on systems that won't boot.</p>
        </div>
      </div>

      {/* Mode tabs */}
      <div style={s.tabs}>
        <button style={{ ...s.tab, ...(mode === "grub" ? s.tabActive : {}) }} onClick={() => setMode("grub")}>
          GRUB Reinstall
        </button>
        <button style={{ ...s.tab, ...(mode === "mbr" ? s.tabActive : {}) }} onClick={() => setMode("mbr")}>
          MBR Repair
        </button>
      </div>

      {/* GRUB form */}
      {step === "select" && mode === "grub" && (
        <div style={s.card}>
          <div style={s.warningBox}>
            <AlertTriangle size={13} color="#F5C842" />
            <span>
              Before running: mount the target system's root partition (e.g. <code style={s.code}>sudo mount /dev/sda2 /mnt</code>)
              and set the chroot path to that mount point.
            </span>
          </div>

          <Field label="Target disk (not partition)" placeholder="/dev/sda"
            value={disk} onChange={setDisk}
            hint="The disk GRUB will be installed on (e.g. /dev/sda, not /dev/sda1)" />

          <Field label="Chroot root (mounted system)" placeholder="/mnt"
            value={chrootRoot} onChange={setChrootRoot}
            hint="Path where the broken system's root partition is mounted" />

          <div style={s.field}>
            <label style={s.label}>Firmware mode</label>
            <div style={s.radioRow}>
              {(["Uefi", "Bios"] as Firmware[]).map(f => (
                <label key={f} style={s.radio} onClick={() => setFirmware(f)}>
                  <div style={s.radioDot(firmware === f)} />
                  <span style={{ color: firmware === f ? "#E8EAF0" : "#8A929E" }}>{f}</span>
                </label>
              ))}
            </div>
          </div>

          {firmware === "Uefi" && (
            <Field label="EFI partition mount point" placeholder="/boot/efi"
              value={efiMount} onChange={setEfiMount}
              hint="Mount the EFI partition here before proceeding" />
          )}

          <button
            style={{ ...s.btn, opacity: (disk && chrootRoot) ? 1 : 0.4 }}
            disabled={!disk || !chrootRoot}
            onClick={() => setStep("confirm")}
          >
            <Play size={14} /> Repair GRUB
          </button>
        </div>
      )}

      {/* MBR form */}
      {step === "select" && mode === "mbr" && (
        <div style={s.card}>
          <Field label="Target disk" placeholder="/dev/sda"
            value={disk} onChange={setDisk}
            hint="MBR bootstrap code will be written to this disk's first sector" />
          <button
            style={{ ...s.btn, opacity: disk ? 1 : 0.4 }}
            disabled={!disk}
            onClick={() => setStep("confirm")}
          >
            <Play size={14} /> Repair MBR
          </button>
        </div>
      )}

      {/* Confirm gate */}
      {step === "confirm" && (
        <ConfirmGate
          device={disk}
          operationLabel={mode === "grub" ? "GRUB Reinstall" : "MBR Bootstrap Repair"}
          operationDesc={
            mode === "grub"
              ? `Reinstall GRUB bootloader on ${disk}. This will overwrite the existing bootloader. The system partition at ${chrootRoot} will be used as the chroot environment.`
              : `Write GRUB bootstrap code to the MBR of ${disk}. Overwrites the first 446 bytes of the disk.`
          }
          onConfirmed={handleConfirmed}
          onCancelled={() => setStep("select")}
        />
      )}

      {/* Running */}
      {step === "running" && (
        <div style={s.card}>
          <div style={{ color: "#F58C1F", fontWeight: 600, marginBottom: "12px" }}>
            Repairing boot — do not interrupt…
          </div>
          <div style={{ color: "#8A929E", fontSize: "12px" }}>
            This may take 1–3 minutes. Interrupting mid-repair can leave the system unbootable.
          </div>
        </div>
      )}

      {/* Done */}
      {step === "done" && result && (
        <div>
          <div style={{ ...s.card, borderColor: result.success ? "#3DB882" : "#E03A3A" }}>
            <div style={s.resultHeader}>
              {result.success
                ? <CheckCircle size={20} color="#3DB882" />
                : <XCircle    size={20} color="#E03A3A" />
              }
              <div style={{ color: result.success ? "#3DB882" : "#E03A3A", fontWeight: 600 }}>
                {result.success ? "Boot repair completed successfully." : "Boot repair encountered errors."}
              </div>
            </div>

            {result.next_steps.length > 0 && (
              <div style={s.nextSteps}>
                <div style={s.nextLabel}>NEXT STEPS</div>
                {result.next_steps.map((step, i) => (
                  <div key={i} style={s.nextItem}>
                    <ChevronRight size={13} color="#8A929E" />
                    <span>{step}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div style={s.outputCard}>
            <div style={s.outputLabel}>Operation Log</div>
            <pre style={s.output}>{result.log}</pre>
          </div>

          <button style={s.btnSecondary} onClick={() => { setStep("select"); setResult(null); }}>
            Start Over
          </button>
        </div>
      )}
    </div>
  );
}

function Field({ label, placeholder, value, onChange, hint }: {
  label: string; placeholder: string; value: string; onChange: (v: string) => void; hint?: string;
}) {
  return (
    <div style={{ marginBottom: "16px" }}>
      <label style={s.label}>{label}</label>
      <input style={s.input} value={value} onChange={e => onChange(e.target.value)}
        placeholder={placeholder} spellCheck={false} />
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
  tabActive:   { backgroundColor: "#1E2329", borderColor: "#F58C1F", color: "#E8EAF0" },
  card:        { backgroundColor: "#161A1F", border: "1px solid #2A2F38", borderRadius: "8px", padding: "20px", marginBottom: "16px" },
  warningBox:  { display: "flex", alignItems: "flex-start", gap: "8px", backgroundColor: "#1A180A", border: "1px solid #F5C842", borderRadius: "6px", padding: "10px 12px", marginBottom: "18px", color: "#8A929E", fontSize: "12px", lineHeight: "1.6" },
  code:        { backgroundColor: "#0D0F12", padding: "1px 5px", borderRadius: "3px", color: "#F58C1F", fontFamily: "monospace" },
  field:       { marginBottom: "16px" },
  label:       { display: "block", color: "#8A929E", fontSize: "11px", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: "6px" },
  input:       { width: "100%", backgroundColor: "#1E2329", border: "1px solid #2A2F38", borderRadius: "6px", padding: "9px 12px", color: "#E8EAF0", fontSize: "13px", fontFamily: "'IBM Plex Mono', monospace", outline: "none" },
  hint:        { display: "block", color: "#4A515C", fontSize: "11px", marginTop: "5px" },
  radioRow:    { display: "flex", gap: "16px" },
  radio:       { display: "flex", alignItems: "center", gap: "8px", cursor: "pointer" },
  radioDot:    (active: boolean) => ({ width: "16px", height: "16px", borderRadius: "50%", border: `2px solid ${active ? "#F58C1F" : "#2A2F38"}`, backgroundColor: active ? "#F58C1F" : "transparent" } as React.CSSProperties),
  btn:         { display: "flex", alignItems: "center", gap: "8px", backgroundColor: "#F58C1F", border: "none", borderRadius: "6px", padding: "10px 18px", color: "#0D0F12", fontSize: "13px", fontWeight: "700", cursor: "pointer", marginTop: "4px" },
  btnSecondary:{ display: "flex", alignItems: "center", gap: "8px", backgroundColor: "#1E2329", border: "1px solid #2A2F38", borderRadius: "6px", padding: "9px 16px", color: "#E8EAF0", fontSize: "13px", cursor: "pointer" },
  resultHeader:{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "14px" },
  nextSteps:   { marginTop: "12px", backgroundColor: "#1E2329", borderRadius: "6px", padding: "12px 14px" },
  nextLabel:   { color: "#4A515C", fontSize: "10px", fontWeight: "700", letterSpacing: "0.12em", textTransform: "uppercase", marginBottom: "8px" },
  nextItem:    { display: "flex", alignItems: "flex-start", gap: "8px", color: "#8A929E", fontSize: "12px", padding: "4px 0", lineHeight: "1.6" },
  outputCard:  { backgroundColor: "#0D0F12", border: "1px solid #2A2F38", borderRadius: "8px", padding: "16px", marginBottom: "16px" },
  outputLabel: { color: "#4A515C", fontSize: "10px", fontWeight: "700", letterSpacing: "0.12em", textTransform: "uppercase", marginBottom: "10px" },
  output:      { color: "#E8EAF0", fontSize: "11px", fontFamily: "'IBM Plex Mono', monospace", whiteSpace: "pre-wrap", wordBreak: "break-all", maxHeight: "300px", overflowY: "auto", lineHeight: "1.7" },
};
