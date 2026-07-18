# Phoenix Key

Phoenix Key is PhoenixCore's desktop recovery and media-planning application. It preserves the **Reignite · Rebuild · Reboot** product identity while enforcing the repository boundary:

- `libbootforge` detects connected USB peripherals and phone service modes.
- PhoenixCore identifies removable media and produces verified, non-destructive build plans.
- Phoenix Key presents both engines through one desktop interface.

This migration phase does not expose physical media writing. Browser mode never fabricates hardware; live results require the Tauri desktop runtime.

## Development

```bash
npm ci
npm run check:boundaries
npm run build
npm run desktop:dev
```

The native build requires Rust, Tauri v1 prerequisites, Python 3, and platform USB dependencies. `libbootforge` is pinned to the proven BootForge commit recorded in `src-tauri/Cargo.toml`.
