# Phoenix OS Scaffold

This directory is the future OS build workspace for Phoenix OS.

Subdirectories:

- `live-build/` - Debian/Ubuntu live image recipes and build profiles.
- `calamares/` - installer configuration and Phoenix-specific install modules.
- `branding/` - visual identity for boot, installer, login, desktop, and defaults.
- `package-lists/` - apt and Flatpak package sets for daily-driver profiles.
- `scripts/` - OS image build, validation, and release helper scripts.

PR 3 creates structure and documentation only. It does not build an ISO, change packages, or migrate app code.
