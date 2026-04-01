# PhoenixCore Companion — Mobile App Design

## App Concept

PhoenixCore Companion is the mobile command center for building the ultimate universal bootable USB. It helps users identify their broken device, select the right operating systems and repair tools, build a "USB recipe," and access a knowledge base of troubleshooting guides. The app is designed for one-handed use in portrait orientation, following Apple Human Interface Guidelines.

---

## Color Palette

| Token | Light | Dark | Purpose |
|-------|-------|------|---------|
| **primary** | `#E85D04` (Phoenix Orange) | `#F48C06` | Brand accent, CTAs, active states |
| **background** | `#FFFFFF` | `#0D1117` | Screen backgrounds |
| **surface** | `#F6F8FA` | `#161B22` | Cards, elevated surfaces |
| **foreground** | `#1B1F23` | `#E6EDF3` | Primary text |
| **muted** | `#656D76` | `#8B949E` | Secondary text, labels |
| **border** | `#D0D7DE` | `#30363D` | Dividers, card borders |
| **success** | `#1A7F37` | `#3FB950` | Compatible, supported |
| **warning** | `#BF8700` | `#D29922` | Partial support, caveats |
| **error** | `#CF222E` | `#F85149` | Incompatible, errors |

The Phoenix Orange brand color evokes fire and rebirth, aligning with the PhoenixCore identity of bringing "dead" devices back to life.

---

## Screen List

### Tab 1: Home (Dashboard)
The landing screen provides a quick overview of PhoenixCore's capabilities and a prominent "Start Building" call-to-action. It shows a hero section with the PhoenixCore tagline, quick-access cards for the main features (Device Wizard, OS Library, Toolkit), and a "Recent Recipes" section for returning users.

### Tab 2: Device Wizard
A step-by-step wizard that helps users identify their target device and its capabilities. The wizard flows through three steps: (1) Select device type (PC/Laptop, Mac, Chromebook, Tablet, Other), (2) Select architecture (x86-64, ARM64, Apple Silicon), and (3) View compatibility results showing which OSes can be installed and which tools are recommended.

### Tab 3: USB Builder
The core feature screen where users assemble their universal USB recipe. It shows a list of available OS installers (Windows 10/11, Ubuntu, Fedora, ChromeOS Flex, macOS Ventura/Sonoma) and repair toolkits (MediCat, Hiren's BootCD PE, Memtest86, GParted). Users toggle items on/off, see estimated USB size, and can export the recipe as a JSON configuration file for the desktop PhoenixCore app.

### Tab 4: Knowledge Base
A searchable library of troubleshooting guides, device compatibility information, and step-by-step tutorials. Categories include: Boot Troubleshooting, OS Installation Guides, OCLP Mac Patching, Driver Issues, and Data Recovery. Each article is a detail screen with rich text content.

### Sub-screens (pushed via navigation)
- **OS Detail Screen:** Shows detailed information about an OS (requirements, supported architectures, download size, known issues).
- **Tool Detail Screen:** Shows detailed information about a repair tool (what it fixes, how to use it, compatibility).
- **Device Compatibility Result:** Shows the full compatibility matrix for a selected device.
- **Recipe Detail / Export:** Shows the final USB recipe with all selected items and an export button.
- **Article Detail:** Full-text view of a knowledge base article.

---

## Key User Flows

### Flow 1: "My Device is Dead — Help Me Fix It"
1. User opens app → Home screen with "Start Building" CTA
2. Taps "Start Building" → Device Wizard (Tab 2)
3. Selects device type (e.g., "Mac")
4. Selects model/architecture (e.g., "Intel Mac — iMac 18,1")
5. Sees compatibility results: macOS Ventura (supported via OCLP), Linux (supported), Windows (supported)
6. Taps "Build USB for This Device" → USB Builder (Tab 3) pre-populated with recommended items
7. Reviews and customizes the recipe
8. Taps "Export Recipe" → JSON file ready to sync with desktop PhoenixCore

### Flow 2: "I Want a Universal USB for Everything"
1. User opens app → Home screen
2. Taps "USB Builder" tab directly
3. Toggles on: Windows 11, Ubuntu 24.04, ChromeOS Flex, MediCat, Hiren's BootCD PE, GParted, Memtest86
4. Sees estimated USB size (e.g., "~64GB recommended")
5. Taps "Export Recipe" → JSON configuration file generated

### Flow 3: "I Need Help Troubleshooting"
1. User opens app → Knowledge Base tab
2. Searches "Mac won't boot"
3. Finds article: "Reviving a Dead Mac with OCLP + PhoenixCore"
4. Reads step-by-step guide with screenshots and tips

---

## Layout Specifications

### Tab Bar
Four tabs at the bottom: Home (house icon), Device Wizard (cpu icon), USB Builder (usb icon), Knowledge Base (book icon). Active tab uses Phoenix Orange tint.

### Cards
All cards use `surface` background, 12px border radius, 1px `border` color border, 16px internal padding. Cards have a subtle shadow on light mode and no shadow on dark mode.

### Typography
- Screen titles: 28px bold
- Section headers: 20px semibold
- Body text: 16px regular
- Captions/labels: 13px regular, `muted` color

### Spacing
- Screen horizontal padding: 16px
- Card gap: 12px
- Section gap: 24px

---

## Data Model (Local — AsyncStorage)

The app stores all data locally using AsyncStorage. No server or database is needed for the core experience.

| Entity | Fields | Storage Key |
|--------|--------|-------------|
| **USB Recipe** | id, name, createdAt, items[], estimatedSize, targetDevice | `@recipes` |
| **Recipe Item** | id, type (os/tool), name, version, size, architecture, selected | Part of Recipe |
| **Device Profile** | type, model, architecture, capabilities | `@device_profiles` |
| **Bookmarked Articles** | articleId[] | `@bookmarks` |

---

## OS & Tool Catalog (Bundled Data)

The app ships with a pre-built catalog of operating systems and repair tools. This data is hardcoded in a TypeScript file and can be updated in future app releases.

### Operating Systems

| OS | Architectures | Size (approx) | Boot Method | Notes |
|----|--------------|----------------|-------------|-------|
| Windows 10 | x86-64 | 5.8 GB | UEFI/Legacy | Requires product key |
| Windows 11 | x86-64 | 6.2 GB | UEFI only | TPM 2.0 required (can bypass) |
| Ubuntu 24.04 LTS | x86-64, ARM64 | 5.7 GB | UEFI/Legacy | Most popular Linux distro |
| Fedora 41 | x86-64, ARM64 | 2.3 GB | UEFI/Legacy | Cutting-edge Linux |
| Linux Mint 22 | x86-64 | 2.8 GB | UEFI/Legacy | Windows-like experience |
| ChromeOS Flex | x86-64 | 1.5 GB | UEFI | Google's free OS for old PCs |
| macOS Ventura | Intel x86-64 | 12.5 GB | OpenCore/OCLP | Requires OCLP for older Macs |
| macOS Sonoma | Intel x86-64 | 13.7 GB | OpenCore/OCLP | Limited older Mac support |
| macOS Sequoia | Apple Silicon | 14.1 GB | Native | Apple Silicon only |
| Asahi Linux | Apple Silicon ARM64 | 3.2 GB | Asahi installer | For Apple Silicon Macs |

### Repair Tools

| Tool | Size (approx) | Purpose |
|------|----------------|---------|
| MediCat USB | 25 GB | All-in-one Windows PE recovery |
| Hiren's BootCD PE | 3.2 GB | Windows repair and diagnostics |
| GParted Live | 0.5 GB | Disk partitioning |
| Memtest86+ | 0.01 GB | RAM testing |
| SystemRescue | 0.8 GB | Linux-based system rescue |
| Clonezilla | 0.4 GB | Disk cloning and imaging |
| ShredOS | 0.05 GB | Secure disk wiping |
