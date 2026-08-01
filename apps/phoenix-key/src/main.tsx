import React, { useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { invoke } from "@tauri-apps/api/tauri";
import "./styles.css";

type View = "devices" | "media";
type DeviceMode = "Normal" | "Recovery" | "Dfu" | "Bootloader" | "Fastboot" | "Adb" | "MassStorage" | "Unknown";

interface DeviceInfo {
  bus_number: number;
  address: number;
  vendor_id: number;
  product_id: number;
  vendor_name?: string | null;
  manufacturer?: string | null;
  product_name?: string | null;
  serial_number?: string | null;
  platform: string;
  transport: string;
  mode: DeviceMode;
  recommended_workflow?: string;
}

interface MediaTarget {
  drive_path: string;
  display_name: string;
  size_human: string;
  is_removable: boolean;
  is_external: boolean;
  is_fixed: boolean;
  is_system: boolean;
  bus_protocol?: string | null;
  confidence: string;
  is_eligible: boolean;
  warnings: string[];
  block_reasons: string[];
}

interface MediaScan {
  schema: string;
  device_count: number;
  devices: MediaTarget[];
  scan_warnings?: string[];
}

interface WritePreparation {
  schema: string;
  target: string;
  target_identity_sha256: string;
  target_size_bytes: number;
  image_path: string;
  image_size_bytes: number;
  authorization_phrase: string;
  write_candidate: boolean;
}

const hex = (value: number) => value.toString(16).padStart(4, "0").toUpperCase();
const isDesktopRuntime = () => "__TAURI__" in window;

function App() {
  const [view, setView] = useState<View>("devices");
  const [devices, setDevices] = useState<DeviceInfo[]>([]);
  const [media, setMedia] = useState<MediaTarget[]>([]);
  const [selectedDevice, setSelectedDevice] = useState<number | null>(null);
  const [selectedMedia, setSelectedMedia] = useState<number | null>(null);
  const [imagePath, setImagePath] = useState("");
  const [plan, setPlan] = useState<Record<string, unknown> | null>(null);
  const [writePreparation, setWritePreparation] = useState<WritePreparation | null>(null);
  const [authorization, setAuthorization] = useState("");
  const [destructiveAcknowledgement, setDestructiveAcknowledgement] = useState(false);
  const [writeReceipt, setWriteReceipt] = useState<Record<string, unknown> | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("Desktop engine required for live hardware results.");

  const activeDevice = selectedDevice === null ? undefined : devices[selectedDevice];
  const activeMedia = selectedMedia === null ? undefined : media[selectedMedia];
  const specialModes = useMemo(
    () => devices.filter((device) => device.mode !== "Normal" && device.mode !== "Unknown").length,
    [devices],
  );

  async function scanDevices() {
    if (!isDesktopRuntime()) {
      setMessage("Live USB scanning is unavailable in a browser. Open Phoenix Key Desktop.");
      return;
    }
    setBusy(true);
    setMessage("BootForge is reading connected USB endpoints…");
    try {
      const result = await invoke<DeviceInfo[]>("scan_connected_devices");
      setDevices(result);
      setSelectedDevice(result.length ? 0 : null);
      setMessage(result.length
        ? `${result.length} actionable service device${result.length === 1 ? "" : "s"} detected.`
        : "No actionable phones, recovery devices, or service-mode hardware detected.");
    } catch (error) {
      setDevices([]);
      setSelectedDevice(null);
      setMessage(`Peripheral scan failed: ${String(error)}`);
    } finally {
      setBusy(false);
    }
  }

  async function scanMedia() {
    if (!isDesktopRuntime()) {
      setMessage("Live media scanning is unavailable in a browser. Open Phoenix Key Desktop.");
      return;
    }
    setBusy(true);
    setPlan(null);
    setWritePreparation(null);
    setWriteReceipt(null);
    setMessage("PhoenixCore is identifying removable media targets…");
    try {
      const result = await invoke<MediaScan>("scan_media_targets");
      setMedia(result.devices);
      setSelectedMedia(result.devices.length ? 0 : null);
      setMessage(`${result.device_count} storage target${result.device_count === 1 ? "" : "s"} inspected.`);
    } catch (error) {
      setMedia([]);
      setSelectedMedia(null);
      setMessage(`Media scan failed: ${String(error)}`);
    } finally {
      setBusy(false);
    }
  }

  async function buildPlan() {
    if (!activeMedia || !imagePath.trim()) return;
    setBusy(true);
    setMessage("PhoenixCore is validating a non-destructive build plan…");
    try {
      const result = await invoke<Record<string, unknown>>("plan_media_build", {
        targetDrive: activeMedia.drive_path,
        imagePath: imagePath.trim(),
      });
      setPlan(result);
      setWritePreparation(null);
      setAuthorization("");
      setDestructiveAcknowledgement(false);
      setWriteReceipt(null);
      setMessage("Dry-run plan generated. No bytes were written.");
    } catch (error) {
      setPlan(null);
      setMessage(`Plan validation failed: ${String(error)}`);
    } finally {
      setBusy(false);
    }
  }

  async function prepareWrite() {
    if (!activeMedia || !imagePath.trim()) return;
    setBusy(true);
    setAuthorization("");
    setDestructiveAcknowledgement(false);
    setWriteReceipt(null);
    setMessage("Re-scanning the physical drive and building an identity-bound authorization…");
    try {
      const result = await invoke<WritePreparation>("prepare_media_write", {
        targetDrive: activeMedia.drive_path,
        imagePath: imagePath.trim(),
      });
      setWritePreparation(result);
      setMessage("Safe-device gate passed. Review the identity and type the exact authorization phrase.");
    } catch (error) {
      setWritePreparation(null);
      setMessage(`Write preparation blocked: ${String(error)}`);
    } finally {
      setBusy(false);
    }
  }

  async function executeWrite() {
    if (!activeMedia || !writePreparation || !destructiveAcknowledgement) return;
    setBusy(true);
    setWriteReceipt(null);
    setMessage("Writing and verifying the selected removable device. Do not disconnect it…");
    try {
      const result = await invoke<Record<string, unknown>>("execute_media_write", {
        targetDrive: activeMedia.drive_path,
        imagePath: imagePath.trim(),
        authorization,
        destructiveAcknowledgement,
      });
      setWriteReceipt(result);
      setMessage("Write completed and full SHA-256 readback verification passed.");
    } catch (error) {
      setMessage(`Physical write blocked or failed: ${String(error)}`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand-mark" aria-hidden="true">P</div>
        <div className="brand-copy"><span>Phoenix Key</span><small>PhoenixCore · powered by BootForge</small></div>
        <nav aria-label="Primary">
          <button className={`nav-item ${view === "devices" ? "active" : ""}`} onClick={() => setView("devices")}><span>⌁</span> Device Forge</button>
          <button className={`nav-item ${view === "media" ? "active" : ""}`} onClick={() => setView("media")}><span>◇</span> Media Builder</button>
          <button className="nav-item" disabled><span>↻</span> Recovery Center</button>
          <button className="nav-item" disabled><span>▦</span> Session History</button>
        </nav>
        <div className="safety-card"><strong>Safe-device writer</strong><p>Only live-verified external USB, SD, or MMC targets can write. Boot, system, internal, ambiguous, or changed devices remain blocked.</p></div>
        <footer>Reignite · Rebuild · Reboot</footer>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div><p className="eyebrow">{view === "devices" ? "CONNECTED DEVICE FORGE" : "PHOENIX MEDIA BUILDER"}</p><h1>{view === "devices" ? "Know what is connected before a tool acts." : "Prove the target and image before a byte moves."}</h1></div>
          <div className="runtime-pill"><i className={isDesktopRuntime() ? "online" : ""} />{isDesktopRuntime() ? "Desktop engine" : "Browser shell only"}</div>
        </header>

        <div className="hero-panel">
          <div><span className="status-label">SYSTEM STATUS</span><h2>{busy ? "Reading the signal…" : "Phoenix Key is standing by."}</h2><p>{message}</p></div>
          <button className="scan-button" onClick={view === "devices" ? scanDevices : scanMedia} disabled={busy}>{busy ? "Scanning…" : view === "devices" ? "Scan Connected Devices" : "Scan Media Targets"}</button>
        </div>

        {view === "devices" ? (
          <>
            <div className="metric-grid"><Metric label="Actionable" value={devices.length.toString()} detail="phones and service devices" /><Metric label="Special modes" value={specialModes.toString()} detail="recovery, DFU, ADB or fastboot" /><Metric label="Engine" value="BOOTFORGE" detail="low-level detection boundary" accent /></div>
            <div className="content-grid">
              <Inventory title="Service-device inventory" count={devices.length} empty="No actionable device is connected. Mouse, keyboard, receivers, hubs, host controllers, and internal USB endpoints are intentionally hidden.">
                {devices.map((device, index) => <button className={`item-row ${selectedDevice === index ? "selected" : ""}`} key={`${device.bus_number}-${device.address}-${device.vendor_id}-${device.product_id}`} onClick={() => setSelectedDevice(index)}><span className="device-orb">{device.platform === "Apple" ? "A" : "U"}</span><span><strong>{device.product_name || "USB Device"}</strong><small>{hex(device.vendor_id)}:{hex(device.product_id)}</small></span><b>{device.mode}</b></button>)}
              </Inventory>
              <section className="details panel"><PanelHeading eyebrow="SIGNAL REPORT" title="Device details" />{activeDevice ? <div className="detail-body"><div className="device-title"><span className="device-orb large">{activeDevice.platform === "Apple" ? "A" : "U"}</span><div><h4>{activeDevice.product_name || "USB Device"}</h4><p>{activeDevice.manufacturer || activeDevice.vendor_name || "Unknown manufacturer"}</p></div></div><dl><Detail label="Hardware ID" value={`${hex(activeDevice.vendor_id)}:${hex(activeDevice.product_id)}`} /><Detail label="Mode" value={activeDevice.mode} /><Detail label="Platform" value={activeDevice.platform} /><Detail label="Transport" value={activeDevice.transport} /><Detail label="Bus / Address" value={`${activeDevice.bus_number} / ${activeDevice.address}`} /><Detail label="Serial" value={activeDevice.serial_number || "Not exposed"} /></dl><div className="recommendation"><span>APPROVED NEXT ROUTE</span><strong>{activeDevice.recommended_workflow || "Standard inspection"}</strong><p>PhoenixCore may route verified, owner-authorized work to a governed tool adapter.</p></div></div> : <Empty text="Select a detected device to open its signal report." />}</section>
            </div>
          </>
        ) : (
          <>
            <div className="metric-grid"><Metric label="Targets" value={media.length.toString()} detail="storage devices inspected" /><Metric label="Eligible" value={media.filter((item) => item.is_eligible).length.toString()} detail="removable, non-system targets" /><Metric label="Write mode" value="GUARDED" detail="safe external devices only" accent /></div>
            <div className="content-grid">
              <Inventory title="Media targets" count={media.length} empty="Connect a removable USB drive, then scan media targets.">
                {media.map((item, index) => <button className={`item-row ${selectedMedia === index ? "selected" : ""}`} key={item.drive_path} onClick={() => { setSelectedMedia(index); setPlan(null); setWritePreparation(null); setAuthorization(""); setDestructiveAcknowledgement(false); setWriteReceipt(null); }}><span className="device-orb">M</span><span><strong>{item.display_name}</strong><small>{item.drive_path} · {item.size_human}</small></span><b className={item.is_eligible ? "good" : "blocked"}>{item.is_eligible ? "Eligible" : "Blocked"}</b></button>)}
              </Inventory>
              <section className="details panel"><PanelHeading eyebrow="BUILD CONTRACT" title="Verified media writer" />{activeMedia ? <div className="detail-body"><dl><Detail label="Target" value={activeMedia.drive_path} /><Detail label="Capacity" value={activeMedia.size_human} /><Detail label="Confidence" value={activeMedia.confidence} /><Detail label="Protocol" value={activeMedia.bus_protocol || "Unknown"} /></dl>{activeMedia.block_reasons.length > 0 && <div className="warning-box"><strong>Target blocked</strong>{activeMedia.block_reasons.map(reason => <p key={reason}>{reason}</p>)}</div>}<label className="path-field"><span>Image path</span><input value={imagePath} onChange={(event) => { setImagePath(event.target.value); setPlan(null); setWritePreparation(null); setAuthorization(""); setDestructiveAcknowledgement(false); setWriteReceipt(null); }} placeholder="C:\\images\\phoenix.iso" /></label><button className="plan-button" onClick={buildPlan} disabled={busy || !activeMedia.is_eligible || !imagePath.trim()}>Generate Dry-Run Plan</button>{plan && <><pre className="plan-output">{JSON.stringify(plan, null, 2)}</pre><button className="prepare-button" onClick={prepareWrite} disabled={busy}>Prepare Safe-Device Write</button></>}{writePreparation && <div className="write-gate"><strong>Permanent erasure warning</strong><p>Phoenix Key will overwrite {writePreparation.target}. Identity: {writePreparation.target_identity_sha256}</p><code>{writePreparation.authorization_phrase}</code><label className="path-field"><span>Type the exact authorization phrase</span><input value={authorization} onChange={(event) => setAuthorization(event.target.value)} /></label><label className="acknowledgement"><input type="checkbox" checked={destructiveAcknowledgement} onChange={(event) => setDestructiveAcknowledgement(event.target.checked)} /><span>I confirm this is the selected removable test device and understand all existing data will be destroyed.</span></label><button className="write-button" onClick={executeWrite} disabled={busy || authorization !== writePreparation.authorization_phrase || !destructiveAcknowledgement}>Erase, Write and Verify</button></div>}{writeReceipt && <pre className="receipt-output">{JSON.stringify(writeReceipt, null, 2)}</pre>}</div> : <Empty text="Select a scanned removable target to prepare a verified media write." />}</section>
            </div>
          </>
        )}
      </section>
    </main>
  );
}

function Metric({ label, value, detail, accent = false }: { label: string; value: string; detail: string; accent?: boolean }) { return <article className={`metric ${accent ? "accent" : ""}`}><span>{label}</span><strong>{value}</strong><p>{detail}</p></article>; }
function PanelHeading({ eyebrow, title }: { eyebrow: string; title: string }) { return <div className="panel-heading"><div><p className="eyebrow">{eyebrow}</p><h3>{title}</h3></div></div>; }
function Inventory({ title, count, empty, children }: { title: string; count: number; empty: string; children: React.ReactNode }) { return <section className="inventory panel"><div className="panel-heading"><div><p className="eyebrow">LIVE HARDWARE</p><h3>{title}</h3></div><span>{count}</span></div>{count === 0 ? <Empty text={empty} /> : <div className="item-rows">{children}</div>}</section>; }
function Empty({ text }: { text: string }) { return <div className="empty-state"><div className="port-icon">⌁</div><p>{text}</p></div>; }
function Detail({ label, value }: { label: string; value: string }) { return <div><dt>{label}</dt><dd>{value}</dd></div>; }

createRoot(document.getElementById("root")!).render(<React.StrictMode><App /></React.StrictMode>);
