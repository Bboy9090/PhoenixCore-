# PhoenixCore Deploy – Zero-Config Guide

Everything builds and deploys automatically. Do a **one-time setup** below, then push to `main` and you're done.

---

## What Runs Automatically

| On push to `main` | Result |
|------------------|--------|
| **Rust** | Builds phoenix-core, phoenix-safety, phoenix-fs-fat32, phoenix-bootloader-core, phoenix-wim |
| **Recovery USB** | Creates `BootForge-Bootable-USB.zip` and `bootable_usb/` |
| **Mobile (web)** | Builds Expo web app and deploys to **GitHub Pages** |

---

## One-Time Setup (5 minutes)

### 1. Enable GitHub Pages

1. Repo → **Settings** → **Pages**
2. **Source:** GitHub Actions
3. Save

After the first deploy, your app will be at: `https://YOUR_USERNAME.github.io/PhoenixCore-/`

### 2. Deploy the Backend (Optional)

The mobile app needs an API. Deploy the Flask backend to [Render.com](https://render.com) (free tier):

1. Sign up at render.com
2. **New** → **Web Service**
3. Connect your GitHub repo
4. Render auto-detects `render.yaml` – use it
5. Deploy. You'll get a URL like `https://phoenixcore-backend.onrender.com`

### 3. Set Backend URL (If you deployed to Render)

1. Repo → **Settings** → **Secrets and variables** → **Actions**
2. Add variable: `BACKEND_URL` = `https://YOUR-RENDER-URL.onrender.com`
3. (Or leave unset – app uses default `https://phoenixcore-backend.onrender.com`)

---

## Manual Triggers

- **Workflow dispatch:** Actions → **Deploy** → **Run workflow**
- **Release:** Create a release on GitHub → artifacts (USB zip, mobile web zip) attach automatically

---

## Local Commands (for reference)

```bash
# Backend
python3 web_server.py

# Mobile (Expo)
cd phoenix-core-mobile && npx expo start

# Recovery USB toolkit
python3 create_recovery_usb.py --yes

# BootForge GUI
python3 main.py --gui
```
