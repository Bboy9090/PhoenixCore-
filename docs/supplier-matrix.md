# Phoenix Supplier Matrix

Goal: every capability Phoenix provides is native.

| Capability | Current implementation (3rd-party name) | Risk (license / reliability / security) | Replacement module | Replacement milestone (date / version) |
|---|---|---|---|---|
| Disk enumeration + removable detection | PowerShell CIM (Get-CimInstance) + psutil in `src/core/hardware_detector.py` | Shell dependency; brittle output parsing; elevated privileges | phoenix-host-windows | M0 |
| Partitioning + formatting | diskpart.exe / format.com in `src/core/usb_builder.py` | Destructive; external tooling; OS-version coupling | phoenix-packs/winpe | M1 |
| Volume mounting | mountvol (Windows), diskutil (macOS), mount/umount (Linux) in `src/recovery/mount.py` | Shell dependency; privilege risk; inconsistent behaviors | phoenix-host-windows (Windows), future providers | M0 (Windows), M2 (cross-platform) |
| Imaging read-only probe + hashing | Python file I/O + PowerShell Dismount-Volume in `src/core/disk_manager.py` | Shell dependency; limited verification; handle conflicts | phoenix-imaging | M0 |
| WIM/ESD handling + driver injection | DISM.exe / wimlib-imagex in `src/core/win_patch_engine.py` | External tools; licensing/reliability; elevated privileges | phoenix-packs/winpe + phoenix-imaging | M1 |
| Windows repair | sfc / dism / bootrec / bcdboot in `src/recovery/windows_repair.py` | External tools; high privilege; OS-version coupling | phoenix-host-windows + phoenix-imaging | M2 |
| Safety gates | Python SafetyValidator + psutil in `src/core/safety_validator.py` | Hard to audit; no formal token flow | phoenix-safety | M0 |
| Evidence reports | Ad-hoc JSON/logging in `src/core/safety_validator.py` | Inconsistent format; no signing | phoenix-report | M0 |
| USB build workflow | Python StorageBuilder in `src/core/usb_builder.py` | Orchestrates external tools; brittle | phoenix-packs/winpe + phoenix-workflow-engine | M1 |
