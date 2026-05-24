export type Architecture = "x86-64" | "ARM64" | "Apple Silicon" | "x86" | "Any";

export type BootMethod = "UEFI" | "Legacy BIOS" | "UEFI/Legacy" | "OpenCore/OCLP" | "Native" | "Asahi Installer" | "Ventoy";

export interface OSItem {
  id: string;
  name: string;
  version: string;
  category: "windows" | "linux" | "macos" | "chromeos";
  architectures: Architecture[];
  sizeGB: number;
  bootMethod: BootMethod;
  description: string;
  requirements: string[];
  notes: string;
  iconName: string;
  color: string;
}

export interface ToolItem {
  id: string;
  name: string;
  version: string;
  category: "recovery" | "diagnostics" | "partitioning" | "cloning" | "security";
  sizeGB: number;
  description: string;
  features: string[];
  iconName: string;
  color: string;
}

export interface DeviceType {
  id: string;
  name: string;
  icon: string;
  architectures: Architecture[];
  description: string;
}

export interface CompatibilityResult {
  osId: string;
  status: "supported" | "partial" | "unsupported";
  notes: string;
}

export const OS_CATALOG: OSItem[] = [
  {
    id: "win10",
    name: "Windows 10",
    version: "22H2",
    category: "windows",
    architectures: ["x86-64"],
    sizeGB: 5.8,
    bootMethod: "UEFI/Legacy",
    description: "The most widely used Windows version, compatible with virtually all x86-64 hardware. Ideal for older PCs that cannot run Windows 11.",
    requirements: ["2 GHz processor", "4 GB RAM", "64 GB storage", "DirectX 9 GPU"],
    notes: "Requires a product key for full activation. Can be installed and used without activation with limited personalization.",
    iconName: "laptop",
    color: "#0078D4",
  },
  {
    id: "win11",
    name: "Windows 11",
    version: "24H2",
    category: "windows",
    architectures: ["x86-64"],
    sizeGB: 6.2,
    bootMethod: "UEFI",
    description: "The latest Windows with modern UI, Copilot AI integration, and enhanced security. Requires UEFI with Secure Boot and TPM 2.0.",
    requirements: ["1 GHz dual-core 64-bit CPU", "4 GB RAM", "64 GB storage", "TPM 2.0", "UEFI Secure Boot"],
    notes: "TPM 2.0 requirement can be bypassed during installation using registry edits. UEFI-only boot.",
    iconName: "laptop",
    color: "#0078D4",
  },
  {
    id: "ubuntu",
    name: "Ubuntu",
    version: "24.04 LTS",
    category: "linux",
    architectures: ["x86-64", "ARM64"],
    sizeGB: 5.7,
    bootMethod: "UEFI/Legacy",
    description: "The most popular Linux distribution, known for ease of use and massive community support. LTS versions receive 5 years of security updates.",
    requirements: ["2 GHz dual-core CPU", "4 GB RAM", "25 GB storage"],
    notes: "Excellent hardware compatibility. Supports both UEFI and Legacy BIOS boot. Live USB mode available for testing without installation.",
    iconName: "terminal",
    color: "#E95420",
  },
  {
    id: "fedora",
    name: "Fedora",
    version: "41",
    category: "linux",
    architectures: ["x86-64", "ARM64"],
    sizeGB: 2.3,
    bootMethod: "UEFI/Legacy",
    description: "A cutting-edge Linux distribution backed by Red Hat. Ships with the latest kernel, GNOME desktop, and developer tools.",
    requirements: ["2 GHz dual-core CPU", "2 GB RAM", "20 GB storage"],
    notes: "Great for developers and users who want the latest software. Shorter support cycle than Ubuntu LTS.",
    iconName: "terminal",
    color: "#51A2DA",
  },
  {
    id: "mint",
    name: "Linux Mint",
    version: "22",
    category: "linux",
    architectures: ["x86-64"],
    sizeGB: 2.8,
    bootMethod: "UEFI/Legacy",
    description: "A user-friendly Linux distribution based on Ubuntu, designed to feel familiar to Windows users. Features the Cinnamon desktop environment.",
    requirements: ["2 GHz dual-core CPU", "2 GB RAM", "20 GB storage"],
    notes: "Best choice for users transitioning from Windows. Includes multimedia codecs out of the box.",
    iconName: "terminal",
    color: "#87CF3E",
  },
  {
    id: "chromeos",
    name: "ChromeOS Flex",
    version: "Latest",
    category: "chromeos",
    architectures: ["x86-64"],
    sizeGB: 1.5,
    bootMethod: "UEFI",
    description: "Google's free operating system designed to breathe new life into old PCs and Macs. Cloud-first, fast boot, and automatic updates.",
    requirements: ["Intel/AMD x86-64 CPU", "4 GB RAM", "16 GB storage"],
    notes: "Does not support Android apps (unlike full ChromeOS). Requires UEFI boot. Excellent for older hardware with limited resources.",
    iconName: "globe",
    color: "#4285F4",
  },
  {
    id: "macos-ventura",
    name: "macOS Ventura",
    version: "13",
    category: "macos",
    architectures: ["x86-64", "Apple Silicon"],
    sizeGB: 12.5,
    bootMethod: "OpenCore/OCLP",
    description: "macOS Ventura with Stage Manager, Continuity Camera, and enhanced security. Supported on Intel Macs via OpenCore Legacy Patcher (OCLP).",
    requirements: ["Intel Mac (2012+) or Apple Silicon", "4 GB RAM", "35 GB storage"],
    notes: "For unsupported Intel Macs, requires OCLP patching via Bobby's PhoenixDrive. Apple Silicon Macs run natively.",
    iconName: "desktop",
    color: "#AC39FF",
  },
  {
    id: "macos-sonoma",
    name: "macOS Sonoma",
    version: "14",
    category: "macos",
    architectures: ["x86-64", "Apple Silicon"],
    sizeGB: 13.7,
    bootMethod: "OpenCore/OCLP",
    description: "macOS Sonoma with desktop widgets, Game Mode, and video conferencing improvements. Limited support on older Intel Macs via OCLP.",
    requirements: ["Intel Mac (2017+) or Apple Silicon", "4 GB RAM", "35 GB storage"],
    notes: "OCLP support for older Intel Macs is more limited than Ventura. Some features may not work on patched systems.",
    iconName: "desktop",
    color: "#AC39FF",
  },
  {
    id: "macos-sequoia",
    name: "macOS Sequoia",
    version: "15",
    category: "macos",
    architectures: ["Apple Silicon"],
    sizeGB: 14.1,
    bootMethod: "Native",
    description: "The latest macOS release, designed exclusively for Apple Silicon Macs. Features iPhone Mirroring, enhanced window tiling, and Apple Intelligence.",
    requirements: ["Apple Silicon Mac (M1 or later)", "8 GB RAM", "35 GB storage"],
    notes: "Apple Silicon only. Cannot be installed on Intel Macs, even with OCLP.",
    iconName: "desktop",
    color: "#AC39FF",
  },
  {
    id: "asahi",
    name: "Asahi Linux",
    version: "Latest",
    category: "linux",
    architectures: ["Apple Silicon"],
    sizeGB: 3.2,
    bootMethod: "Asahi Installer",
    description: "A Linux distribution specifically built for Apple Silicon Macs. Provides native ARM64 Linux with GPU acceleration on M1/M2/M3 chips.",
    requirements: ["Apple Silicon Mac", "16 GB free storage"],
    notes: "Dual-boots alongside macOS. Uses its own installer (not a standard ISO). GPU drivers are still maturing.",
    iconName: "terminal",
    color: "#FF6B6B",
  },
];

export const TOOL_CATALOG: ToolItem[] = [
  {
    id: "medicat",
    name: "MediCat USB",
    version: "2024",
    category: "recovery",
    sizeGB: 25,
    description: "The ultimate all-in-one Windows PE recovery toolkit. Includes hundreds of portable tools for virus removal, password reset, disk repair, and data recovery.",
    features: ["Windows 10/11 PE environment", "Malwarebytes portable", "Password reset tools", "Disk repair utilities", "Data recovery software", "PortableApps suite"],
    iconName: "healing",
    color: "#E53935",
  },
  {
    id: "ventoy-mac",
    name: "Ventoy for macOS",
    version: "1.0.99",
    category: "recovery" as const,
    sizeGB: 0.02,
    description: "Native macOS Ventoy installer — no Windows required. Uses Ventoy2Disk.sh to set up multi-boot USB drives directly on your Mac with full UEFI + Legacy BIOS support.",
    features: [
      "Native macOS shell script (Ventoy2Disk.sh)",
      "No Windows VM or Boot Camp needed",
      "Full UEFI + Legacy BIOS support",
      "Secure Boot compatible (with MOK enrollment)",
      "Supports 1100+ tested ISOs",
      "GPT + MBR partition schemes",
      "Drop ISOs directly — no reflashing",
      "Works on Apple Silicon + Intel Mac",
    ],
    iconName: "storage",
    color: "#00d2ff",
  },
  {
    id: "hirens",
    name: "Hiren's BootCD PE",
    version: "1.0.8",
    category: "recovery",
    sizeGB: 3.2,
    description: "A curated Windows 10 PE-based recovery disk with essential free tools for hardware diagnostics, data recovery, and system repair.",
    features: ["Windows 10 PE environment", "Hardware diagnostics", "Data recovery tools", "Registry editor", "Disk management", "Network tools"],
    iconName: "build",
    color: "#1565C0",
  },
  {
    id: "gparted",
    name: "GParted Live",
    version: "1.6",
    category: "partitioning",
    sizeGB: 0.5,
    description: "A lightweight Linux-based partition editor for creating, resizing, moving, and deleting disk partitions. Essential for multi-boot setups.",
    features: ["Partition create/resize/move/delete", "Filesystem support (NTFS, ext4, FAT32, HFS+)", "Disk health checks", "Partition recovery"],
    iconName: "storage",
    color: "#43A047",
  },
  {
    id: "memtest",
    name: "Memtest86+",
    version: "7.0",
    category: "diagnostics",
    sizeGB: 0.01,
    description: "The industry-standard memory testing tool. Boots independently of any OS to perform thorough RAM diagnostics and detect faulty memory modules.",
    features: ["Comprehensive RAM testing", "Multiple test algorithms", "Error detection and reporting", "No OS required"],
    iconName: "memory",
    color: "#FF8F00",
  },
  {
    id: "systemrescue",
    name: "SystemRescue",
    version: "11.0",
    category: "recovery",
    sizeGB: 0.8,
    description: "A Linux-based system rescue toolkit for repairing unbootable systems, recovering data, and managing partitions. Includes a full Linux environment.",
    features: ["Linux rescue environment", "Filesystem repair (fsck)", "Network tools", "Disk cloning", "Antivirus scanning"],
    iconName: "restore",
    color: "#7B1FA2",
  },
  {
    id: "clonezilla",
    name: "Clonezilla",
    version: "3.1",
    category: "cloning",
    sizeGB: 0.4,
    description: "A free disk cloning and imaging tool. Create full disk backups, clone drives, and deploy system images across multiple machines.",
    features: ["Disk-to-disk cloning", "Disk image creation", "Network multicast deployment", "Supports MBR and GPT"],
    iconName: "content-copy",
    color: "#00838F",
  },
  {
    id: "shredos",
    name: "ShredOS",
    version: "2024",
    category: "security",
    sizeGB: 0.05,
    description: "A secure disk wiping tool based on nwipe. Permanently erases all data on a drive using military-grade wiping algorithms.",
    features: ["DoD 5220.22-M wiping", "Gutmann 35-pass method", "PRNG stream wiping", "Verification pass", "Certificate of erasure"],
    iconName: "delete-forever",
    color: "#D32F2F",
  },
];

export const DEVICE_TYPES: DeviceType[] = [
  {
    id: "pc-laptop",
    name: "PC / Laptop",
    icon: "laptop",
    architectures: ["x86-64"],
    description: "Standard Windows or Linux PC/laptop with Intel or AMD processor. Supports the widest range of operating systems and tools.",
  },
  {
    id: "intel-mac",
    name: "Intel Mac",
    icon: "desktop",
    architectures: ["x86-64"],
    description: "Apple Mac with Intel processor (pre-2020). Supports macOS via OCLP, Windows via Boot Camp, and Linux natively.",
  },
  {
    id: "apple-silicon-mac",
    name: "Apple Silicon Mac",
    icon: "desktop",
    architectures: ["Apple Silicon"],
    description: "Apple Mac with M1, M2, M3, or M4 chip. Supports macOS natively and Asahi Linux. Limited Windows support (ARM only via Parallels).",
  },
  {
    id: "chromebook-x86",
    name: "Chromebook (Intel/AMD)",
    icon: "laptop",
    architectures: ["x86-64"],
    description: "Chromebook with Intel or AMD processor. Can run ChromeOS, ChromeOS Flex, and some Linux distributions.",
  },
  {
    id: "chromebook-arm",
    name: "Chromebook (ARM)",
    icon: "laptop",
    architectures: ["ARM64"],
    description: "Chromebook with ARM processor. Limited to ChromeOS and some ARM Linux distributions. Cannot run Windows or x86 software.",
  },
  {
    id: "raspberry-pi",
    name: "Raspberry Pi / SBC",
    icon: "developer-board",
    architectures: ["ARM64"],
    description: "Single-board computer with ARM processor. Supports Raspberry Pi OS, Ubuntu ARM, and other ARM Linux distributions.",
  },
];

export function getCompatibility(deviceId: string): CompatibilityResult[] {
  const device = DEVICE_TYPES.find((d) => d.id === deviceId);
  if (!device) return [];

  return OS_CATALOG.map((os) => {
    const archMatch = os.architectures.some((a) => device.architectures.includes(a));

    if (!archMatch) {
      return { osId: os.id, status: "unsupported" as const, notes: `Incompatible architecture. ${os.name} requires ${os.architectures.join(" or ")}.` };
    }

    // Special cases
    if (deviceId === "intel-mac" && os.category === "macos") {
      if (os.id === "macos-sequoia") {
        return { osId: os.id, status: "unsupported" as const, notes: "macOS Sequoia requires Apple Silicon. Not available for Intel Macs." };
      }
      return { osId: os.id, status: "partial" as const, notes: "Requires OpenCore Legacy Patcher (OCLP) via Bobby's PhoenixDrive for unsupported models." };
    }

    if (deviceId === "apple-silicon-mac") {
      if (os.category === "windows") {
        return { osId: os.id, status: "unsupported" as const, notes: "x86 Windows cannot run natively on Apple Silicon. Use Parallels or UTM for virtualization." };
      }
      if (os.id === "asahi") {
        return { osId: os.id, status: "supported" as const, notes: "Asahi Linux runs natively on Apple Silicon with dual-boot alongside macOS." };
      }
      if (os.category === "linux" && os.id !== "asahi") {
        return { osId: os.id, status: "unsupported" as const, notes: "Standard x86 Linux cannot boot on Apple Silicon. Use Asahi Linux instead." };
      }
    }

    if (deviceId === "chromebook-arm") {
      if (os.category !== "linux" || !os.architectures.includes("ARM64")) {
        return { osId: os.id, status: "unsupported" as const, notes: "ARM Chromebooks can only run ARM-compatible Linux distributions." };
      }
    }

    if (deviceId === "chromebook-x86" && os.category === "macos") {
      return { osId: os.id, status: "unsupported" as const, notes: "macOS cannot be installed on Chromebooks (requires Apple hardware or Hackintosh setup)." };
    }

    return { osId: os.id, status: "supported" as const, notes: "Fully compatible. Can be booted and installed from USB." };
  });
}

export interface KBArticle {
  id: string;
  title: string;
  category: string;
  summary: string;
  content: string;
  tags: string[];
}

export const KB_ARTICLES: KBArticle[] = [
  {
    id: "ventoy-multiboot",
    title: "Creating a Multi-Boot USB with Ventoy",
    category: "USB Creation",
    summary: "Learn how to use Ventoy to create a single USB drive that can boot multiple operating systems and tools without reformatting — including native macOS support.",
    content: `Ventoy is the foundation of a universal bootable USB. Unlike traditional tools like Rufus or Etcher that format the USB for a single ISO, Ventoy creates a special boot partition that can detect and boot ANY ISO file you copy to the drive.

**How It Works:**
1. Install Ventoy on your USB drive (this only needs to be done once)
2. Copy ISO files directly to the USB — no special formatting needed
3. Boot from the USB and select which ISO to launch from Ventoy's menu

**macOS Native Mode (No Windows Required):**
Phoenix Core includes Ventoy for macOS — run it directly on your Mac:

  # Download Ventoy
  curl -LO https://github.com/ventoy/Ventoy/releases/latest/download/ventoy-1.0.99-mac.tar.gz
  tar -xf ventoy-1.0.99-mac.tar.gz
  cd ventoy-1.0.99

  # Install to USB (replace disk2 with your disk number)
  sudo sh Ventoy2Disk.sh -i /dev/disk2

  # Update existing Ventoy installation (preserves your ISOs)
  sudo sh Ventoy2Disk.sh -u /dev/disk2

  # UEFI-only mode (recommended for modern hardware)
  sudo sh Ventoy2Disk.sh -i -u /dev/disk2

Phoenix Core auto-detects macOS and uses Ventoy2Disk.sh automatically during the USB build process.

**Windows Setup (Alternative):**
1. Download Ventoy from ventoy.net
2. Run Ventoy2Disk.exe (Windows GUI)
3. Select your USB drive and click "Install"

**Step-by-Step macOS Setup via Phoenix Core:**
1. Open Phoenix Core → USB Builder tab
2. Select your OS images and tools
3. Select your USB drive from the scan
4. Phoenix Core detects macOS and uses Ventoy2Disk.sh
5. Progress shows: Partitioning → Ventoy install → ISO copy → Verify
6. Done — boot your USB on any machine!

**Supported Formats:** ISO, WIM, IMG, VHD(x), EFI files
**Compatibility:** Legacy BIOS, UEFI, Secure Boot (with MOK enrollment)
**Tested ISOs:** 1100+ distributions and tools verified

**Pro Tips:**
- Use a 128GB+ USB 3.0/3.1 drive for best results
- Organize ISOs in folders (e.g., /Windows, /Linux, /Phoenix, /Tools)
- Ventoy supports persistence for Linux live sessions
- On Apple Silicon Mac, use disk identifier from: diskutil list
- Ventoy updates are non-destructive — your ISOs stay intact`,
    tags: ["ventoy", "multi-boot", "usb", "iso", "macos", "mac-native"],
  },
  {
    id: "dead-mac-oclp",
    title: "Reviving a Dead Mac with OCLP + Bobby's PhoenixDrive",
    category: "Mac Recovery",
    summary: "Step-by-step guide to using OpenCore Legacy Patcher through Bobby's PhoenixDrive to install modern macOS on unsupported Intel Macs.",
    content: `If you have an older Mac that Apple has dropped support for, OpenCore Legacy Patcher (OCLP) can bring it back to life with the latest macOS versions. Bobby's PhoenixDrive integrates OCLP directly into its USB building workflow.

**Supported Macs (via OCLP):**
- iMac (2012-2019)
- MacBook Pro (2012-2019)
- MacBook Air (2012-2019)
- Mac mini (2012-2018)
- Mac Pro (2010-2019)

**The Process:**
1. Open Bobby's PhoenixDrive on a working Mac
2. Select your target Mac model (e.g., iMac 18,1)
3. Choose macOS version (Ventura recommended for best compatibility)
4. Bobby's PhoenixDrive downloads the installer and applies OCLP patches
5. Write to USB drive
6. Boot the dead Mac from the USB (hold Option key at startup)
7. Install macOS
8. Run OCLP post-install patches for full hardware support

**Common Issues:**
- Graphics acceleration may require specific kext patches
- Wi-Fi/Bluetooth may need additional drivers for older chipsets
- Some features (AirDrop, Handoff) may not work on very old models
- Always back up data before attempting recovery

**Bobby's PhoenixDrive Advantage:**
Bobby's PhoenixDrive automates the OCLP configuration, including kext selection, SIP settings, and SecureBootModel configuration. What normally takes hours of manual setup is reduced to a few clicks.`,
    tags: ["mac", "oclp", "recovery", "phoenixcore", "macos"],
  },
  {
    id: "windows-repair",
    title: "Repairing Windows with a Bootable USB",
    category: "Windows Recovery",
    summary: "How to use Windows Recovery Environment, Hiren's BootCD PE, and MediCat to fix common Windows boot failures.",
    content: `When Windows won't boot, a bootable USB with the right tools can save the day. Here are three approaches, from simplest to most powerful.

**Approach 1: Windows Recovery Environment (Built-in)**
If you have a Windows installation USB:
1. Boot from the USB
2. Click "Repair your computer" instead of "Install"
3. Choose Troubleshoot > Advanced Options
4. Try: Startup Repair, System Restore, or Command Prompt
5. In Command Prompt, try: bootrec /fixmbr, bootrec /fixboot, bootrec /rebuildbcd

**Approach 2: Hiren's BootCD PE (Lightweight)**
A curated Windows 10 PE environment with essential tools:
1. Boot from Hiren's USB
2. Use Mini Windows 10 to access the broken system's files
3. Run disk check: chkdsk C: /f /r
4. Use registry editor to fix boot configuration
5. Run Malwarebytes portable for virus scanning

**Approach 3: MediCat USB (Nuclear Option)**
The most comprehensive toolkit available:
1. Boot into MediCat's Windows 11 PE environment
2. Access hundreds of portable tools
3. Reset passwords with NTPWEdit or Lazesoft
4. Recover data with Recuva or TestDisk
5. Clone the drive with Macrium Reflect PE
6. Wipe and reinstall if all else fails

**When Nothing Works:**
If the drive is physically failing (clicking sounds, not detected in BIOS), no software tool can help. Consider professional data recovery services.`,
    tags: ["windows", "repair", "boot", "recovery", "medicat", "hirens"],
  },
  {
    id: "chromeos-flex-guide",
    title: "Installing ChromeOS Flex on Old Hardware",
    category: "ChromeOS",
    summary: "Turn any old PC or Mac into a fast Chromebook using Google's free ChromeOS Flex.",
    content: `ChromeOS Flex is Google's free operating system designed to give old computers a second life. It's lightweight, boots fast, and receives automatic updates.

**Requirements:**
- x86-64 processor (Intel or AMD)
- 4 GB RAM minimum
- 16 GB storage minimum
- USB drive (8 GB+) for installation

**Creating the Installer:**
Option A — Chrome Recovery Utility (easiest):
1. Install the Chrome Recovery Utility extension
2. Select "Google ChromeOS Flex" as manufacturer
3. Select "ChromeOS Flex" as product
4. Insert USB and create the installer

Option B — Manual (for advanced users):
1. Download the ChromeOS Flex image from Google
2. Use dd (Linux/Mac) or Rufus (Windows) to write to USB

**Installation:**
1. Boot from the USB (press F12/F2/Del at startup)
2. Choose "Install ChromeOS Flex" or "Try it first"
3. Follow the setup wizard
4. Sign in with your Google account

**What You Get:**
- Chrome browser with full extension support
- Google Drive integration
- Linux development environment (Crostini)
- Automatic security updates for 10 years

**What You Don't Get:**
- Android app support (only on official Chromebooks)
- Some hardware may lack driver support (check Google's certified list)`,
    tags: ["chromeos", "flex", "installation", "old-hardware"],
  },
  {
    id: "ventoy-mac-native",
    title: "Ventoy for Mac — Build USBs Without Windows",
    category: "USB Creation",
    summary: "Complete guide to using Ventoy's native macOS shell script to create bootable USB drives on your Mac — no Windows environment, Boot Camp, or VM required.",
    content: `Phoenix Core integrates Ventoy for macOS directly into its build pipeline. When running on a Mac, the USB Builder automatically switches to Ventoy2Disk.sh instead of the Windows executable.

**Why Ventoy on Mac?**
Traditionally, creating a Ventoy USB required Windows. Ventoy's macOS shell script (Ventoy2Disk.sh) changes that — it runs natively on both Intel and Apple Silicon Macs with full UEFI and Legacy BIOS support.

**What Phoenix Core Does Automatically:**
1. Detects you're on macOS (web, iOS, or native)
2. Switches build stages to macOS-native workflow
3. Shows "Ventoy2Disk.sh" in the build progress instead of Windows steps
4. Runs: diskutil unmountDisk, Ventoy2Disk.sh, cp (ISO copy), sync, diskutil eject

**Manual Setup (if running outside Phoenix Core):**

Step 1 — Find your USB drive:
  diskutil list
  (Look for your USB — it will show as /dev/disk2, /dev/disk3, etc.)

Step 2 — Download Ventoy for Mac:
  curl -LO https://github.com/ventoy/Ventoy/releases/latest/download/ventoy-1.0.99-mac.tar.gz
  tar -xf ventoy-1.0.99-mac.tar.gz
  cd ventoy-1.0.99

Step 3 — Install Ventoy to your USB:
  sudo sh Ventoy2Disk.sh -i /dev/disk2

Step 4 — Update existing Ventoy (preserves ISOs):
  sudo sh Ventoy2Disk.sh -u /dev/disk2

Step 5 — Copy your ISO files:
  cp ~/Downloads/ubuntu-24.04.iso /Volumes/Ventoy/
  cp ~/Downloads/blue-phoenix-os.iso /Volumes/Ventoy/Phoenix/

Step 6 — Safe eject:
  diskutil eject /dev/disk2

**Apple Silicon Notes:**
- Ventoy works on M1/M2/M3/M4 Macs
- The USB can boot x86-64 ISOs on OTHER machines (not the M-series Mac itself)
- For booting on Apple Silicon, use macOS Recovery or Asahi Linux installer

**Secure Boot:**
If the target machine uses Secure Boot, enroll the Ventoy MOK key:
  1. Boot from Ventoy USB
  2. Select "Enroll Key" on first boot
  3. Follow MOK manager prompts
  4. Reboot — Secure Boot now accepts Ventoy

**Phoenix Core Integration:**
In the USB Builder, when "Ventoy for macOS" is in your tool selection and you're on a Mac, the build simulation shows the exact Ventoy2Disk.sh command being run. The complete command is shown in the Recipe Preview step so you can verify it before building.`,
    tags: ["ventoy", "macos", "mac-native", "apple-silicon", "intel-mac", "usb", "no-windows"],
  },
  {
    id: "linux-rescue",
    title: "Linux System Rescue and Data Recovery",
    category: "Linux Recovery",
    summary: "Using SystemRescue and other Linux tools to recover data and repair broken Linux installations.",
    content: `When a Linux system won't boot, SystemRescue provides a complete rescue environment with all the tools you need.

**Boot into SystemRescue:**
1. Create a SystemRescue USB (use Ventoy or dd)
2. Boot from the USB
3. You'll get a full Linux environment with root access

**Common Repairs:**

Fixing GRUB bootloader:
  mount /dev/sda2 /mnt
  mount /dev/sda1 /mnt/boot/efi
  grub-install --root-directory=/mnt /dev/sda
  chroot /mnt update-grub

Checking filesystem:
  fsck -y /dev/sda2

Recovering deleted files:
  testdisk /dev/sda (for partition recovery)
  photorec /dev/sda (for file recovery)

Resetting root password:
  mount /dev/sda2 /mnt
  chroot /mnt
  passwd root

**Data Recovery Priority:**
1. Do NOT write anything to the affected drive
2. Use ddrescue to create a disk image first
3. Run recovery tools on the image, not the original drive
4. TestDisk for partition recovery, PhotoRec for files`,
    tags: ["linux", "rescue", "recovery", "grub", "systemrescue"],
  },
  {
    id: "universal-usb-architecture",
    title: "Understanding CPU Architecture and Boot Compatibility",
    category: "Technical",
    summary: "Why a truly universal USB is limited by CPU architecture, and how Bobby's PhoenixDrive bridges the gap.",
    content: `The dream of a single USB that boots everything on every device is limited by one fundamental constraint: CPU architecture.

**The Architecture Problem:**
Computers use different instruction sets:
- x86-64 (Intel/AMD): Most PCs, laptops, and Intel Macs
- ARM64 (Apple Silicon, Qualcomm): Apple M-series Macs, some Chromebooks, phones
- ARM (32-bit): Older Chromebooks, Raspberry Pi (older models)

A bootloader compiled for x86-64 physically cannot execute on an ARM processor. It's like trying to play a Blu-ray in a cassette player — the hardware doesn't understand the format.

**What Bobby's PhoenixDrive Does:**
Instead of trying to be one impossible USB, Bobby's PhoenixDrive helps you build the RIGHT USB for your specific device:

For x86-64 devices (covers ~85% of computers):
- Windows 10/11, any Linux distro, ChromeOS Flex, macOS (Intel Macs)
- All repair tools (MediCat, Hiren's, GParted, etc.)
- One USB can hold ALL of these via Ventoy

For Apple Silicon Macs:
- macOS (native)
- Asahi Linux (native ARM64)
- Separate USB needed due to different boot process

For ARM Chromebooks:
- ChromeOS recovery
- ARM Linux distributions
- Very limited tool selection

**The Bobby's PhoenixDrive Solution:**
The mobile companion app identifies your device, determines its architecture, and builds a custom USB recipe with every compatible OS and tool. It's not one USB for everything — it's the smartest possible USB for YOUR device.`,
    tags: ["architecture", "x86", "arm", "compatibility", "universal"],
  },
];
