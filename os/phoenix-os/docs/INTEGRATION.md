# Phoenix OS Integration Strategy

## Package Flow
Phoenix platform components are integrated into the live image via the following flow:
1. **Compilation**: Rust and React components are built in the monorepo root.
2. **Packaging**: Binaries and assets are bundled into `.deb` packages or directory overlays.
3. **Inclusion**: Package names are added to `packages/phoenix.list`.
4. **Overlaying**: Configuration files (e.g., systemd units, KDE configs) are placed in `overlays/`.

## Future Installer Strategy
While current builds focus on live-media execution, a future **"Phoenix Safe-Installer"** is planned:
- **Non-Destructive**: Will prioritize side-by-side installations.
- **Agent-Governed**: All partition changes must be authorized by the Phoenix Agent.
- **Signed Manifests**: Only signed OS images can be installed.

## Unsupported Features (Alpha)
- Secure Boot customization (Placeholder only)
- Custom kernel modules
- Direct binary execution bypassing the Agent
- Persistent user storage (Encrypted persistence planned for Beta)

## Known Limitations
- Wayland performance on NVIDIA hardware (legacy drivers required).
- High memory usage during live-build process.
- No automated driver interrogation during build-time (runtime only).
