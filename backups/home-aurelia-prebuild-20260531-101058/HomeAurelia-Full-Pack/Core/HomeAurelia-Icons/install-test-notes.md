# ⚙️ KDE Plasma Icon Installation & Verification Test Notes

This guide provides technical validation procedures and installation commands to register, activate, and audit the **Home Aurelia** flagship icon theme on a live Linux system running KDE Plasma.

---

## 📂 1. Directory Structure Specifications

KDE Plasma reads custom icon packages from two standard search paths:
*   **System-Wide**: `/usr/share/icons/home-aurelia/`
*   **User-Specific**: `~/.local/share/icons/home-aurelia/`

We support two distinct packaging formats of the shared Core icon pack:
1.  **Clean Theme (`HomeAurelia-Icons-Clean.zip`)**: strictly focused category folders.
2.  **MaxCompat Theme (`HomeAurelia-Icons-MaxCompat.zip`)**: broad category duplicates.

---

## 💿 2. Technical Installation Instructions

To verify the installation on any target machine, execute the following commands in the terminal:

### Step 2.1: Extract the Theme Package
```bash
# Extract the Clean version into your local user directory
unzip HomeAurelia-Icons-Clean.zip -d ~/.local/share/icons/
```

### Step 2.2: Force Rebuild the KDE Icon Cache
KDE uses an memory-mapped binary cache (`icon-theme.cache`) to load images instantly. Rebuild this cache to ensure Plasma picks up the new paths:
```bash
# Compile and write the standard theme cache binary
gtk-update-icon-cache -f -t ~/.local/share/icons/HomeAurelia-Icons-Clean/
```

### Step 2.3: Reload the KDE Plasma Desktop Compositor
```bash
# Force the system shell to re-read and apply all icon changes
kquitapp5 plasmashell && kstart5 plasmashell &
```

---

## 🔎 3. Verification & Live Auditing Checks

Run these diagnostic commands to confirm successful system-wide loading:

### Check 3.1: Verify in KDE System Settings (KCM)
To confirm the theme appears in KDE System Settings, query the KCM registry:
```bash
# Lists all registered icon themes recognized by KDE System Settings
kcmshell5 kcm_icons --list | grep "Home Aurelia"
```
*Expected Output*:
*   `Home Aurelia Icons (Clean)`
*   `Home Aurelia Icons (MaxCompat)`

### Check 3.2: Verify Dolphin File Manager Placement
Check if Dolphin maps directories to your custom places folder SVGs:
```bash
# Returns the active icon name mapped to your personal Documents folder
xdg-mime query default inode/directory
```

### Check 3.3: Verify System Tray Applet Mappings
Verify that status icons (like wifi and bluetooth) resolve to active Home Aurelia assets:
```bash
# Check loaded symbols in active panel compositor memory
qdbus org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.showInteractiveInterface | grep "home-aurelia"
```
