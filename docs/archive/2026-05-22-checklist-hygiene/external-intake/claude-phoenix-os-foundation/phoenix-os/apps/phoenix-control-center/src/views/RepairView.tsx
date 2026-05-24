import { useState } from "react";
import { Wrench, HardDrive, Search, ShieldCheck, Terminal, ExternalLink, AlertTriangle } from "lucide-react";
import SectionHeader from "../components/SectionHeader";

interface Tool {
  id:       string;
  name:     string;
  desc:     string;
  cmd:      string;
  category: "disk" | "data" | "boot" | "system" | "security";
  danger:   boolean;
}

const TOOLS: Tool[] = [
  // Disk tools
  { id: "gparted",     name: "GParted",          desc: "Graphical partition editor. View and modify partition tables.",                      cmd: "sudo gparted",                 category: "disk",     danger: false },
  { id: "smartctl",    name: "S.M.A.R.T. Scan",  desc: "Run a comprehensive SMART health check on all drives.",                            cmd: "sudo smartctl -a /dev/sda",    category: "disk",     danger: false },
  { id: "fsck",        name: "Filesystem Check",  desc: "Check and repair a filesystem. Requires the filesystem to be unmounted.",          cmd: "sudo fsck -n /dev/sda1",       category: "disk",     danger: true  },
  { id: "testdisk",    name: "TestDisk",           desc: "Recover lost partitions and fix boot sectors. CLI-based guided recovery.",         cmd: "sudo testdisk",                category: "disk",     danger: false },
  { id: "ddrescue",    name: "GNU ddrescue",       desc: "Image a failing drive, skipping bad sectors. Output to an image file.",           cmd: "sudo ddrescue",                category: "data",     danger: false },
  // Data recovery
  { id: "photorec",    name: "PhotoRec",           desc: "Recover lost files (photos, docs, video) by file signature scanning.",           cmd: "sudo photorec",                category: "data",     danger: false },
  { id: "foremost",    name: "Foremost",           desc: "File carving tool. Recovers files based on headers and footers.",                cmd: "sudo foremost",                category: "data",     danger: false },
  // Boot repair
  { id: "grub-repair", name: "GRUB Repair",        desc: "Reinstall GRUB bootloader on a target disk. Use Phoenix Recovery for guided UI.", cmd: "sudo grub-install",            category: "boot",     danger: true  },
  { id: "efibootmgr",  name: "EFI Boot Manager",   desc: "View and modify UEFI boot entries.",                                             cmd: "sudo efibootmgr -v",           category: "boot",     danger: false },
  { id: "chntpw",      name: "chntpw",             desc: "Reset Windows NT/10/11 user passwords via registry editing.",                   cmd: "sudo chntpw",                  category: "system",   danger: true  },
  // Security
  { id: "clamav",      name: "ClamAV Scan",         desc: "Scan a mounted filesystem for viruses and malware.",                            cmd: "sudo clamscan -r /mnt",        category: "security", danger: false },
];

const CATEGORIES = [
  { id: "disk",     label: "Disk",          icon: HardDrive    },
  { id: "data",     label: "Data Recovery", icon: Search       },
  { id: "boot",     label: "Boot Repair",   icon: Terminal     },
  { id: "system",   label: "System",        icon: Wrench       },
  { id: "security", label: "Security",      icon: ShieldCheck  },
] as const;

export default function RepairView() {
  const [activeCategory, setActiveCategory] = useState<string>("disk");

  const filtered = TOOLS.filter(t => t.category === activeCategory);

  return (
    <div style={s.page}>
      <SectionHeader
        title="Repair"
        subtitle="Launch repair and recovery tools"
        icon={<Wrench size={18} color="#F58C1F" />}
      />

      <div style={s.notice}>
        <AlertTriangle size={13} color="#F5C842" />
        <span>Tools marked <span style={{ color: "#E03A3A", fontWeight: 600 }}>Destructive</span> will prompt for confirmation. Never run on a disk you haven't identified.</span>
      </div>

      <div style={s.layout}>
        {/* Category nav */}
        <nav style={s.catNav}>
          {CATEGORIES.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              style={{ ...s.catBtn, ...(activeCategory === id ? s.catBtnActive : {}) }}
              onClick={() => setActiveCategory(id)}
            >
              <Icon size={14} color={activeCategory === id ? "#F58C1F" : "#8A929E"} />
              <span style={{ color: activeCategory === id ? "#E8EAF0" : "#8A929E" }}>{label}</span>
            </button>
          ))}
        </nav>

        {/* Tool list */}
        <div style={s.toolList}>
          {filtered.map(tool => (
            <ToolCard key={tool.id} tool={tool} />
          ))}
        </div>
      </div>
    </div>
  );
}

function ToolCard({ tool }: { tool: Tool }) {
  const [hovered, setHovered] = useState(false);

  const launch = () => {
    // TODO: Invoke shell command via Tauri shell plugin
    // For destructive tools, show confirmation dialog first
    if (tool.danger) {
      const confirmed = window.confirm(
        `"${tool.name}" can modify or erase data.\n\nCommand: ${tool.cmd}\n\nOpen a terminal to run this manually?`
      );
      if (!confirmed) return;
    }
    // TODO: open terminal with pre-filled command via tauri shell
    console.log(`Launch: ${tool.cmd}`);
  };

  return (
    <div
      style={{ ...s.tool, ...(hovered ? s.toolHover : {}) }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <div style={s.toolInfo}>
        <div style={s.toolName}>
          {tool.name}
          {tool.danger && (
            <span style={s.dangerTag}>
              <AlertTriangle size={10} />
              Destructive
            </span>
          )}
        </div>
        <div style={s.toolDesc}>{tool.desc}</div>
        <code style={s.toolCmd}>{tool.cmd}</code>
      </div>
      <button style={s.launchBtn} onClick={launch}>
        <ExternalLink size={13} />
        Launch
      </button>
    </div>
  );
}

const s: Record<string, React.CSSProperties> = {
  page:       { padding: "28px 32px", height: "100%", overflowY: "auto" },
  notice:     { display: "flex", alignItems: "center", gap: "8px", backgroundColor: "#1A180A", border: "1px solid #F5C842", borderRadius: "6px", padding: "8px 12px", marginBottom: "20px", color: "#8A929E", fontSize: "12px" },
  layout:     { display: "grid", gridTemplateColumns: "180px 1fr", gap: "16px", alignItems: "start" },
  catNav:     { display: "flex", flexDirection: "column", gap: "2px" },
  catBtn:     { display: "flex", alignItems: "center", gap: "8px", padding: "9px 12px", borderRadius: "6px", border: "none", background: "transparent", cursor: "pointer", textAlign: "left", fontSize: "13px", width: "100%" },
  catBtnActive: { backgroundColor: "#1E2329", borderLeft: "2px solid #F58C1F", paddingLeft: "10px" },
  toolList:   { display: "flex", flexDirection: "column", gap: "8px" },
  tool:       { display: "flex", justifyContent: "space-between", alignItems: "center", backgroundColor: "#161A1F", border: "1px solid #2A2F38", borderRadius: "8px", padding: "14px 16px", transition: "border-color 0.15s" },
  toolHover:  { borderColor: "#F58C1F" },
  toolInfo:   { flex: 1 },
  toolName:   { display: "flex", alignItems: "center", gap: "10px", color: "#E8EAF0", fontSize: "14px", fontWeight: "600", marginBottom: "4px" },
  dangerTag:  { display: "flex", alignItems: "center", gap: "4px", color: "#E03A3A", fontSize: "10px", border: "1px solid #E03A3A", borderRadius: "4px", padding: "2px 6px" },
  toolDesc:   { color: "#8A929E", fontSize: "12px", marginBottom: "6px", maxWidth: "520px", lineHeight: "1.5" },
  toolCmd:    { color: "#F58C1F", fontSize: "11px", backgroundColor: "#1E2329", padding: "2px 8px", borderRadius: "3px", fontFamily: "'IBM Plex Mono', monospace" },
  launchBtn:  { display: "flex", alignItems: "center", gap: "6px", backgroundColor: "#1E2329", border: "1px solid #2A2F38", borderRadius: "6px", padding: "8px 14px", color: "#E8EAF0", fontSize: "12px", cursor: "pointer", marginLeft: "16px", whiteSpace: "nowrap" },
};
