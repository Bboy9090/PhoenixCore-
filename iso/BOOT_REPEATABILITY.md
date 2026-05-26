# Boot Repeatability

Generated: 2026-05-25T13:35:20Z

This file records attempt-level evidence. Canonical boot status is only allowed to improve when a stronger attempt is observed.

## home - bwos-home.iso

- SHA256: `431e2f39f58c51ecd540dca756d1cf6807ae7add730b7b769546d56432942f13`
- Canonical class: `BOOT_FAIL_DISPLAY`
- Desktop repeatable: `False`
- Shutdown clean: `False`
- Shutdown method: `forced kill`
- Repeatability risk: `False`
- Desktop + shutdown same attempt: `False`
- Desktop + wallpaper + shutdown same attempt: `False`
- Desktop marker attempts: `0`
- Wallpaper marker attempts: `0`
- Presentation lock attempts: `0`
- Shutdown marker attempts: `0`
- Clean shutdown attempts: `0`
- Session determinism class: `NOT_RUN`
- Session desktop markers: `0` / `3`
- Session wallpaper markers: `0` / `3`
- Session presentation lock markers: `0` / `3`
- Wallpaper marker reached: `False`
- Session shutdown markers: `0`

| Attempt | Timestamp | Result Stage | Desktop | Desktop Marker | Wallpaper Marker | Presentation Lock | Shutdown Marker | Clean Shutdown | Canonical Update | Screenshot | Reason/Note | Console Log | Serial Log |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-05-25T13:35:20Z | 2026-05-25T13:39:13Z | BOOT_FAIL_DISPLAY | False | False | False | False | False | False | True |  | desktop | iso/outputs/vm-boot-evidence/home/20260525T133913Z/console.log | iso/outputs/vm-boot-evidence/home/20260525T133913Z/serial.log |

## home - bwos-home.iso

- SHA256: `4998fefa5d115ca6ef05d0c35ec627e976254e42855444bc5035d7c8eb624e5c`
- Canonical class: `BOOT_FAIL_DISPLAY`
- Desktop repeatable: `False`
- Shutdown clean: `False`
- Shutdown method: `forced kill`
- Repeatability risk: `False`
- Desktop + shutdown same attempt: `False`
- Desktop + wallpaper + shutdown same attempt: `False`
- Desktop marker attempts: `0`
- Wallpaper marker attempts: `0`
- Presentation lock attempts: `0`
- Shutdown marker attempts: `0`
- Clean shutdown attempts: `0`
- Session determinism class: `NOT_RUN`
- Session desktop markers: `0` / `3`
- Session wallpaper markers: `0` / `3`
- Session presentation lock markers: `0` / `3`
- Wallpaper marker reached: `False`
- Session shutdown markers: `0`

| Attempt | Timestamp | Result Stage | Desktop | Desktop Marker | Wallpaper Marker | Presentation Lock | Shutdown Marker | Clean Shutdown | Canonical Update | Screenshot | Reason/Note | Console Log | Serial Log |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-05-25T12:16:55Z | 2026-05-25T12:21:01Z | BOOT_FAIL_DISPLAY | False | False | False | False | False | False | True |  | desktop | iso/outputs/vm-boot-evidence/home/20260525T122101Z/console.log | iso/outputs/vm-boot-evidence/home/20260525T122101Z/serial.log |

## home - bwos-home.iso

- SHA256: `807ff8f8b76d92cfd7be8755adcda876865dfec2174f7d4d3451888975818b02`
- Canonical class: `BOOT_FAIL_DISPLAY`
- Desktop repeatable: `False`
- Shutdown clean: `False`
- Shutdown method: `forced kill`
- Repeatability risk: `False`
- Desktop + shutdown same attempt: `False`
- Desktop + wallpaper + shutdown same attempt: `False`
- Desktop marker attempts: `0`
- Wallpaper marker attempts: `0`
- Presentation lock attempts: `0`
- Shutdown marker attempts: `0`
- Clean shutdown attempts: `0`
- Session determinism class: `NOT_RUN`
- Session desktop markers: `0` / `3`
- Session wallpaper markers: `0` / `3`
- Session presentation lock markers: `0` / `3`
- Wallpaper marker reached: `False`
- Session shutdown markers: `0`

| Attempt | Timestamp | Result Stage | Desktop | Desktop Marker | Wallpaper Marker | Presentation Lock | Shutdown Marker | Clean Shutdown | Canonical Update | Screenshot | Reason/Note | Console Log | Serial Log |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-05-25T10:52:00Z | 2026-05-25T10:56:03Z | BOOT_FAIL_DISPLAY | False | False | False | False | False | False | True |  | desktop | iso/outputs/vm-boot-evidence/home/20260525T105603Z/console.log | iso/outputs/vm-boot-evidence/home/20260525T105603Z/serial.log |

## home - bwos-home.iso

- SHA256: `ae023f8aeac29990799b22fb7b64af1f349a89be4b947021488318eb7eba9705`
- Canonical class: `BOOT_PASS_DESKTOP`
- Desktop repeatable: `False`
- Shutdown clean: `False`
- Shutdown method: `forced kill`
- Repeatability risk: `True`
- Desktop + shutdown same attempt: `False`
- Desktop + wallpaper + shutdown same attempt: `False`
- Desktop marker attempts: `2`
- Wallpaper marker attempts: `2`
- Presentation lock attempts: `1`
- Shutdown marker attempts: `0`
- Clean shutdown attempts: `0`
- Session determinism class: `PARTIAL`
- Session desktop markers: `1` / `3`
- Session wallpaper markers: `1` / `3`
- Session presentation lock markers: `1` / `3`
- Wallpaper marker reached: `True`
- Session shutdown markers: `0`

| Attempt | Timestamp | Result Stage | Desktop | Desktop Marker | Wallpaper Marker | Presentation Lock | Shutdown Marker | Clean Shutdown | Canonical Update | Screenshot | Reason/Note | Console Log | Serial Log |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| canonical-2026-05-25T06:10:52Z | 2026-05-25T06:10:52Z | NOT_TESTED | False | False | False | False | False | False | True |  |  |  |  |
| canonical-2026-05-25T06:11:06Z | 2026-05-25T06:11:06Z | NOT_TESTED | False | False | False | False | False | False | True |  |  |  |  |
| PR39I-HOME-AURELIA-PRESENTATION-LOCK | 2026-05-25T06:20:57Z | BOOT_PASS_DESKTOP | True | True | True | True | False | False | True |  | timeout | iso/outputs/vm-boot-evidence/home/20260525T062057Z/console.log | iso/outputs/vm-boot-evidence/home/20260525T062057Z/serial.log |
| PR39J-HOME-X11-SHUTDOWN-PROBE | 2026-05-25T06:46:24Z | BOOT_FAIL_DISPLAY | False | False | False | False | False | False | False |  | desktop | iso/outputs/vm-boot-evidence/home/20260525T064624Z/console.log | iso/outputs/vm-boot-evidence/home/20260525T064624Z/serial.log |
| PR39J-HOME-X11-SAME-ATTEMPT-ACPI | 2026-05-25T09:20:52Z | BOOT_PASS_DESKTOP | True | True | True | False | False | False | False |  | timeout | iso/outputs/vm-boot-evidence/home/20260525T092052Z/console.log | iso/outputs/vm-boot-evidence/home/20260525T092052Z/serial.log |

### PR39E/PR39F/PR39I Session Determinism Attempts

| Attempt | Timestamp | Requested Profile | Selected Session | Actual Type | Actual SDDM Session | Shutdown Probe Cmdline | Desktop Marker | Wallpaper Marker | Presentation Lock | Shutdown Marker | Shutdown | Probe Class | Session Logs | Console Log | Serial Log | Reason/Note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PR39I-HOME-AURELIA-PRESENTATION-LOCK | 2026-05-25T06:20:57Z | x11 | plasma.desktop | x11 | plasma.desktop | False | True | True | True | False | False | WAYLAND_FAIL_X11_PASS | iso/outputs/vm-boot-evidence/home/20260525T062057Z/session.log | iso/outputs/vm-boot-evidence/home/20260525T062057Z/console.log | iso/outputs/vm-boot-evidence/home/20260525T062057Z/serial.log | timeout |

## home - bwos-home.iso

- SHA256: `f113419abc4ad8c343cedb00a667e64fd13076f3c2ed87e658b63dea8059806d`
- Canonical class: `BOOT_FAIL_DISPLAY`
- Desktop repeatable: `False`
- Shutdown clean: `False`
- Shutdown method: `forced kill`
- Repeatability risk: `False`
- Desktop + shutdown same attempt: `False`
- Desktop + wallpaper + shutdown same attempt: `False`
- Desktop marker attempts: `0`
- Wallpaper marker attempts: `0`
- Presentation lock attempts: `0`
- Shutdown marker attempts: `0`
- Clean shutdown attempts: `0`
- Session determinism class: `NOT_RUN`
- Session desktop markers: `0` / `3`
- Session wallpaper markers: `0` / `3`
- Session presentation lock markers: `0` / `3`
- Wallpaper marker reached: `False`
- Session shutdown markers: `0`

| Attempt | Timestamp | Result Stage | Desktop | Desktop Marker | Wallpaper Marker | Presentation Lock | Shutdown Marker | Clean Shutdown | Canonical Update | Screenshot | Reason/Note | Console Log | Serial Log |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PR39H-X11-GUARDED-SHUTDOWN-PROBE | 2026-05-24T20:43:04Z | BOOT_FAIL_DISPLAY | False | False | False | False | False | False | True |  | desktop | iso/outputs/vm-boot-evidence/home/20260524T204304Z/console.log | iso/outputs/vm-boot-evidence/home/20260524T204304Z/serial.log |

## blue-phoenix - bwos-aurelia.iso

- SHA256: `6dcc401780d286353861b275a0c7e960679631b86a89afef57fdfcb41cb8e0e1`
- Canonical class: `NOT_TESTED`
- Desktop repeatable: `False`
- Shutdown clean: `False`
- Shutdown method: `n/a`
- Repeatability risk: `False`
- Desktop + shutdown same attempt: `False`
- Desktop + wallpaper + shutdown same attempt: `False`
- Desktop marker attempts: `0`
- Wallpaper marker attempts: `0`
- Presentation lock attempts: `0`
- Shutdown marker attempts: `0`
- Clean shutdown attempts: `0`
- Session determinism class: `NOT_RUN`
- Session desktop markers: `0` / `3`
- Session wallpaper markers: `0` / `3`
- Session presentation lock markers: `0` / `3`
- Wallpaper marker reached: `False`
- Session shutdown markers: `0`

| Attempt | Timestamp | Result Stage | Desktop | Desktop Marker | Wallpaper Marker | Presentation Lock | Shutdown Marker | Clean Shutdown | Canonical Update | Screenshot | Reason/Note | Console Log | Serial Log |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| canonical-2026-05-25T06:10:52Z | 2026-05-25T06:10:52Z | NOT_TESTED | False | False | False | False | False | False | True |  |  |  |  |
| canonical-2026-05-25T06:11:06Z | 2026-05-25T06:11:06Z | NOT_TESTED | False | False | False | False | False | False | True |  |  |  |  |

## arcwyre - bwos-arcwyre.iso

- SHA256: `3ba79189b56384cec2095fcc008781b87f9d613545b05b8e9c84767492d685fb`
- Canonical class: `NOT_TESTED`
- Desktop repeatable: `False`
- Shutdown clean: `False`
- Shutdown method: `n/a`
- Repeatability risk: `False`
- Desktop + shutdown same attempt: `False`
- Desktop + wallpaper + shutdown same attempt: `False`
- Desktop marker attempts: `0`
- Wallpaper marker attempts: `0`
- Presentation lock attempts: `0`
- Shutdown marker attempts: `0`
- Clean shutdown attempts: `0`
- Session determinism class: `NOT_RUN`
- Session desktop markers: `0` / `3`
- Session wallpaper markers: `0` / `3`
- Session presentation lock markers: `0` / `3`
- Wallpaper marker reached: `False`
- Session shutdown markers: `0`

| Attempt | Timestamp | Result Stage | Desktop | Desktop Marker | Wallpaper Marker | Presentation Lock | Shutdown Marker | Clean Shutdown | Canonical Update | Screenshot | Reason/Note | Console Log | Serial Log |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| canonical-2026-05-25T06:10:52Z | 2026-05-25T06:10:52Z | NOT_TESTED | False | False | False | False | False | False | True |  |  |  |  |
| canonical-2026-05-25T06:11:06Z | 2026-05-25T06:11:06Z | NOT_TESTED | False | False | False | False | False | False | True |  |  |  |  |

## thunder-god - bwos-thunder-god.iso

- SHA256: `4ea3fa9cfa922a3c50138dbd8784442afd89167acd52c8ceffed3882d07eb7d3`
- Canonical class: `NOT_TESTED`
- Desktop repeatable: `False`
- Shutdown clean: `False`
- Shutdown method: `n/a`
- Repeatability risk: `False`
- Desktop + shutdown same attempt: `False`
- Desktop + wallpaper + shutdown same attempt: `False`
- Desktop marker attempts: `0`
- Wallpaper marker attempts: `0`
- Presentation lock attempts: `0`
- Shutdown marker attempts: `0`
- Clean shutdown attempts: `0`
- Session determinism class: `NOT_RUN`
- Session desktop markers: `0` / `3`
- Session wallpaper markers: `0` / `3`
- Session presentation lock markers: `0` / `3`
- Wallpaper marker reached: `False`
- Session shutdown markers: `0`

| Attempt | Timestamp | Result Stage | Desktop | Desktop Marker | Wallpaper Marker | Presentation Lock | Shutdown Marker | Clean Shutdown | Canonical Update | Screenshot | Reason/Note | Console Log | Serial Log |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| canonical-2026-05-25T06:10:52Z | 2026-05-25T06:10:52Z | NOT_TESTED | False | False | False | False | False | False | True |  |  |  |  |
| canonical-2026-05-25T06:11:06Z | 2026-05-25T06:11:06Z | NOT_TESTED | False | False | False | False | False | False | True |  |  |  |  |

## home-legacy-i386 - bwos-home-legacy-i386.img

- SHA256: `70b8efd70b5a3ef0f919cd0f9b6058641c06b56e8cf39aa7290636c6df8207f7`
- Canonical class: `NOT_TESTED`
- Desktop repeatable: `False`
- Shutdown clean: `False`
- Shutdown method: `n/a`
- Repeatability risk: `False`
- Desktop + shutdown same attempt: `False`
- Desktop + wallpaper + shutdown same attempt: `False`
- Desktop marker attempts: `0`
- Wallpaper marker attempts: `0`
- Presentation lock attempts: `0`
- Shutdown marker attempts: `0`
- Clean shutdown attempts: `0`
- Session determinism class: `NOT_RUN`
- Session desktop markers: `0` / `3`
- Session wallpaper markers: `0` / `3`
- Session presentation lock markers: `0` / `3`
- Wallpaper marker reached: `False`
- Session shutdown markers: `0`

| Attempt | Timestamp | Result Stage | Desktop | Desktop Marker | Wallpaper Marker | Presentation Lock | Shutdown Marker | Clean Shutdown | Canonical Update | Screenshot | Reason/Note | Console Log | Serial Log |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| canonical-2026-05-25T06:10:52Z | 2026-05-25T06:10:52Z | NOT_TESTED | False | False | False | False | False | False | True |  |  |  |  |
| canonical-2026-05-25T06:11:06Z | 2026-05-25T06:11:06Z | NOT_TESTED | False | False | False | False | False | False | True |  |  |  |  |

