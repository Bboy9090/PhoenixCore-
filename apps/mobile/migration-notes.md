# Phoenix Mobile Migration Notes

Current source candidates:

- Root Expo app: `app/`, `App.tsx`, `index.tsx`, and root Expo config.
- Secondary mobile app: `mobile/`.
- Duplicate/experimental mobile app: `phoenix-core-mobile/`.
- Legacy integration copies: `legacy/Integrate Backend and USB Features in Phoenix Core App/`.

Migration rule:

Choose one canonical Expo source after comparing routes, API clients, and unique screens. Keep generated native folders out of Git unless a future PR explicitly changes the mobile build strategy.

Not migrated in PR 3:

- Expo routes and screens.
- API clients.
- Native mobile folders.
- Legacy mobile references.
