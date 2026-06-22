# Arcwyre Flex Web App Center Validation

This document registers the validation results of the native Web App Center included in **Arcwyre Flex** release candidate 1 (RC1).

---

## 1. Web App Center Validation Results

The CLI web application provisioning tool `/usr/bin/web-app-center` was tested and audited:

| Functionality | CLI Action | Validation Status | Verification Note |
| :--- | :--- | :--- | :--- |
| **List Catalog** | `web-app-center list` | **PASS** | Successfully lists all 8 default cloud utility definitions. |
| **Install Web App** | `web-app-center install <id>` | **PASS** | Generates XDG-compliant `.desktop` launcher and records registry. |
| **Remove Web App** | `web-app-center remove <id>` | **PASS** | Deletes targeted `.desktop` file and removes registry entry. |
| **List Installed** | `web-app-center installed` | **PASS** | Correctly lists active, installed web apps. |

---

## 2. Desktop Launcher Validation

The generated `.desktop` entries (located under `~/.local/share/applications/`) were validated for XDG specification compliance:

```text
[Desktop Entry]
Version=1.0
Name=ChatGPT
Comment=AI assistant by OpenAI
Exec=firefox --new-window https://chat.openai.com
Icon=chatgpt
Terminal=false
Type=Application
Categories=Productivity;WebApp;
StartupNotify=true
```

- **Compliance**: `PASS` (Correctly integrates with the XFCE applications menu, application finder, and desktop panel shortcuts).
- **Execution Path**: Launches Firefox ESR in a clean, dedicated application window (`--new-window` command line argument).
