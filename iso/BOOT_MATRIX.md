# VM Boot Matrix

Generated: 2026-05-24T21:04:05Z

VM policy: EFI on, Secure Boot off, 4096 MB RAM minimum, 2 CPU cores minimum, and no host disk or USB passthrough.

## VM Tool Audit

| Tool | Availability | Version | Limitations |
|---|---|---|---|
| virtualbox | available | 7.2.6r172322 | Apple Silicon builds are not the primary path for x86_64/i386 boot automation; use for arm64 guests only when explicitly needed. |
| utm | available | 4.7.5 | No native CLI automation is wired into this repository; use manually if needed. |
| qemu | available | QEMU emulator version 11.0.0 | x86 guests run under TCG on Apple Silicon and are slow; arm64 is supported only when the matching firmware is present. |

| Edition ID | Artifact Filename | Path | Format | Size Bytes | SHA256 | Build Summary | Build Status | Telemetry | VM Tool | EFI | Secure Boot | RAM | CPU | Disk | Attempts | Desktop Repeatable | Repeatability Risk | Desktop Marker | Wallpaper Marker | Shutdown Marker | Desktop+Shutdown Same Attempt | Desktop+Wallpaper+Shutdown Same Attempt | Desktop Marker Attempts | Wallpaper Marker Attempts | Shutdown Marker Attempts | Clean Shutdown Attempts | Session Class | Session Probe | Session Desktop Marker Count | Session Wallpaper Marker Count | Shutdown Clean | Shutdown Method | Boot Menu | Kernel | Initramfs | Display Manager | Desktop | Class | Failure Point |
|---|---|---|---|---:|---|---|---|---|---|---|---|---:|---:|---|---:|---|---|---|---|---|---|---|---:|---:|---:|---:|---|---|---:|---:|---|---|---|---|---|---|---|---|
| home | bwos-home.iso | `os/phoenix-os/build/bwos-home.iso` | iso | 2276358144 | `f113419abc4ad8c343cedb00a667e64fd13076f3c2ed87e658b63dea8059806d` | `os/phoenix-os/build/build-summary.json` | completed | recorded | qemu-system-x86_64 | True | disabled | 4096 | 2 | none | 1 | False | False | False | False | False | False | False | 0 | 0 | 0 | 0 | NOT_RUN | MARKER_HOOK_FAIL | 0 | 0 | False | forced kill | True | True | True | True | False | BOOT_FAIL_DISPLAY | desktop |
| blue-phoenix | bwos-aurelia.iso | `os/phoenix-os/build/bwos-aurelia.iso` | iso | 2181836800 | `6dcc401780d286353861b275a0c7e960679631b86a89afef57fdfcb41cb8e0e1` | `os/phoenix-os/build/build-summary.json` | completed | recorded | qemu-system-x86_64 | True | disabled | 4096 | 2 | none | 2 | False | False | False | False | False | False | False | 0 | 0 | 0 | 0 | NOT_RUN | NOT_RUN | 0 | 0 | False |  | False | False | False | False | False | NOT_TESTED |  |
| arcwyre | bwos-arcwyre.iso | `os/phoenix-os/build/bwos-arcwyre.iso` | iso | 2198011904 | `3ba79189b56384cec2095fcc008781b87f9d613545b05b8e9c84767492d685fb` | `os/phoenix-os/build/build-summary.json` | completed | recorded | qemu-system-x86_64 | True | disabled | 4096 | 2 | none | 2 | False | False | False | False | False | False | False | 0 | 0 | 0 | 0 | NOT_RUN | NOT_RUN | 0 | 0 | False |  | False | False | False | False | False | NOT_TESTED |  |
| thunder-god | bwos-thunder-god.iso | `os/phoenix-os/build/bwos-thunder-god.iso` | iso | 2171047936 | `4ea3fa9cfa922a3c50138dbd8784442afd89167acd52c8ceffed3882d07eb7d3` | `os/phoenix-os/build/build-summary.json` | completed | recorded | qemu-system-x86_64 | True | disabled | 4096 | 2 | none | 2 | False | False | False | False | False | False | False | 0 | 0 | 0 | 0 | NOT_RUN | NOT_RUN | 0 | 0 | False |  | False | False | False | False | False | NOT_TESTED |  |
| home-legacy-i386 | bwos-home-legacy-i386.img | `os/phoenix-os/build/bwos-home-legacy-i386.img` | dd-image | 2244222976 | `70b8efd70b5a3ef0f919cd0f9b6058641c06b56e8cf39aa7290636c6df8207f7` | `os/phoenix-os/build/build-summary.json` | completed | recorded | qemu-system-i386 | False | disabled | 4096 | 2 | raw-image | 2 | False | False | False | False | False | False | False | 0 | 0 | 0 | 0 | NOT_RUN | NOT_RUN | 0 | 0 | False |  | False | False | False | False | False | NOT_TESTED |  |
