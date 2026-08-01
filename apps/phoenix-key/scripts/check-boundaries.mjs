import { readFileSync } from "node:fs";

const ui = readFileSync(new URL("../src/main.tsx", import.meta.url), "utf8");
const rust = readFileSync(new URL("../src-tauri/src/main.rs", import.meta.url), "utf8");
const evidence = readFileSync(new URL("../../../scripts/hardware/capture_windows_drive_evidence.py", import.meta.url), "utf8");
const writer = readFileSync(new URL("../../../scripts/hardware/write_windows_sacrificial_drive.py", import.meta.url), "utf8");
const tauri = JSON.parse(readFileSync(new URL("../src-tauri/tauri.conf.json", import.meta.url), "utf8"));

const failures = [];
if (ui.includes("demoDevices") || ui.includes("DEMO-DEVICE")) failures.push("production UI contains demo hardware");
if (!rust.includes("scan_connected_devices")) failures.push("BootForge peripheral scanner is not wired");
if (!rust.includes("filter(is_actionable_device)")) failures.push("raw USB endpoints are not filtered from Device Forge");
if (!rust.includes('matches!(mode.as_str(), "normal" | "unknown")')) failures.push("normal and unknown endpoint filter is missing");
if (!ui.includes("Mouse, keyboard, receivers, hubs, host controllers, and internal USB endpoints are intentionally hidden.")) failures.push("service-device empty-state disclosure is missing");
if (!rust.includes("scan_media_targets")) failures.push("PhoenixCore media scanner is not wired");
if (!rust.includes("plan_media_build")) failures.push("PhoenixCore dry-run planner is not wired");
if (!rust.includes("--plan-write")) failures.push("media planner does not use PhoenixCore dry-run contract");
if (!rust.includes("prepare_media_write")) failures.push("safe-device write preparation is not wired");
if (!rust.includes("execute_media_write")) failures.push("safe-device physical writer is not wired");
if (!rust.includes("destructive_acknowledgement")) failures.push("backend destructive acknowledgement is missing");
if (!evidence.includes('EXTERNAL_BUS_TYPES = {"USB", "SD", "MMC"}')) failures.push("external bus allowlist is missing");
if (!evidence.includes('target-is-boot-disk') || !evidence.includes('target-is-system-disk')) failures.push("boot/system target blocks are missing");
if (!evidence.includes('target-is-read-only')) failures.push("read-only target block is missing");
if (!evidence.includes('stable-device-identity-missing')) failures.push("stable target identity gate is missing");
if (!writer.includes("verify_live_identity")) failures.push("immediate pre-write identity rescan is missing");
if (!writer.includes("Full read-back SHA-256")) failures.push("full readback verification is missing");
if (!writer.includes("byte_cap")) failures.push("image-sized write cap is missing");
if (tauri.tauri.allowlist.all || tauri.tauri.allowlist.shell.all) failures.push("Tauri shell allowlist is open");
if (!ui.includes("Erase, Write and Verify")) failures.push("guarded physical write action is missing");
if (!ui.includes("authorization !== writePreparation.authorization_phrase")) failures.push("UI identity-bound authorization gate is missing");

if (failures.length) {
  console.error(failures.join("\n"));
  process.exit(1);
}
console.log("Phoenix Key repository boundaries verified.");
