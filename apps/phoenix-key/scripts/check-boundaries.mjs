import { readFileSync } from "node:fs";

const ui = readFileSync(new URL("../src/main.tsx", import.meta.url), "utf8");
const rust = readFileSync(new URL("../src-tauri/src/main.rs", import.meta.url), "utf8");
const tauri = JSON.parse(readFileSync(new URL("../src-tauri/tauri.conf.json", import.meta.url), "utf8"));

const failures = [];
if (ui.includes("demoDevices") || ui.includes("DEMO-DEVICE")) failures.push("production UI contains demo hardware");
if (!rust.includes("scan_connected_devices")) failures.push("BootForge peripheral scanner is not wired");
if (!rust.includes("scan_media_targets")) failures.push("PhoenixCore media scanner is not wired");
if (!rust.includes("plan_media_build")) failures.push("PhoenixCore dry-run planner is not wired");
if (!rust.includes("--plan-write")) failures.push("media planner does not use PhoenixCore dry-run contract");
if (tauri.tauri.allowlist.all || tauri.tauri.allowlist.shell.all) failures.push("Tauri shell allowlist is open");
if (ui.toLowerCase().includes("write usb") || ui.toLowerCase().includes("flash usb")) failures.push("production UI exposes a physical write action");

if (failures.length) {
  console.error(failures.join("\n"));
  process.exit(1);
}
console.log("Phoenix Key repository boundaries verified.");
