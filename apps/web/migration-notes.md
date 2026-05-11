# Phoenix Web Migration Notes

Current source candidates:

- Vite recovery GUI: `website/recovery-gui/`.
- Website server: `website/web_server.py`.
- Standalone dashboard: `usb_creation_dashboard.html`.
- Existing deployment docs and config at the repo root.

Migration rule:

Move web surfaces only after deciding which pages belong in public web, docs, support, or archive. Phoenix Web should not become a second desktop app or a recovery-only portal.

Not migrated in PR 3:

- Vite recovery GUI.
- Standalone dashboard.
- Web server.
- Deployment config.
