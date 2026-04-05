# STOP — non-core template at repository root

If your checkout has **`package.json`**, **`pnpm-lock.yaml`**, **`server/_core/`**, or similar at the **repository root**, that tree is **not** the Phoenix Core USB product.

| Use instead |
|-------------|
| **Mobile:** `phoenix-core-mobile/` |
| **API:** `backend/` |
| **Desktop:** `desktop/` + root `main.py` |
| **Shared safety:** `packages/phoenix_safety/` |

Do **not** add Phoenix USB features to the root template without an explicit product decision.

See **`docs/REPO_STATUS_MAP.md`** and **`ROOT_NONCORE_NOTICE.md`**.
