# Quick Deployment Commands Reference

**Copy & paste ready commands for deploying Bobby's PhoenixDrive**

---

## Backend Deployment (Vercel + Supabase)

### 1. Setup

```bash
# Navigate to project
cd /home/ubuntu/phoenix-core-mobile

# Create environment file from template
cp .env.production.example .env.production

# Edit with your credentials
nano .env.production
```

### 2. Automated Deployment

```bash
# Run automated deployment script (recommended)
./deploy-vercel-automated.sh
```

### 3. Manual Deployment

```bash
# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login

# Deploy
vercel --prod

# View logs
vercel logs
```

### 4. Verify Deployment

```bash
# Test health endpoint
curl https://phoenix-drive-api.vercel.app/api/v1/health

# Test database connection
curl https://phoenix-drive-api.vercel.app/api/v1/database/status

# Test hardware detection
curl https://phoenix-drive-api.vercel.app/api/v1/hardware/detect
```

---

## Desktop App Building

### Windows

```bash
# Install dependencies
pip install pyinstaller==6.0.0

# Build executable
pyinstaller --name "PhoenixDrive" \
  --onefile \
  --windowed \
  --icon assets/images/icon.ico \
  main_enhanced.py

# Create installer (requires NSIS)
makensis installer.nsi

# Sign executable (optional)
signtool sign /f certificate.pfx /p password dist/PhoenixDrive.exe

# Generate checksum
sha256sum dist/PhoenixDrive-Setup-2.0.0.exe > dist/PhoenixDrive-Setup-2.0.0.exe.sha256
```

### macOS

```bash
# Install Xcode tools
xcode-select --install

# Build app bundle
pyinstaller --name "PhoenixDrive" \
  --onefile \
  --windowed \
  --icon assets/images/icon.icns \
  --osx-bundle-identifier "com.phoenixdrive.app" \
  main_enhanced.py

# Code sign
codesign --deep --force --verify --verbose \
  --sign "Developer ID Application" \
  dist/PhoenixDrive.app

# Create DMG
create-dmg \
  --volname "PhoenixDrive" \
  --volicon "assets/images/icon.icns" \
  dist/PhoenixDrive-2.0.0.dmg \
  dist/PhoenixDrive.app

# Notarize (requires Apple Developer Account)
xcrun altool --notarize-app \
  --file dist/PhoenixDrive-2.0.0.dmg \
  --primary-bundle-id com.phoenixdrive.app \
  -u your-apple-id@apple.com \
  -p your-app-password

# Generate checksum
sha256sum dist/PhoenixDrive-2.0.0.dmg > dist/PhoenixDrive-2.0.0.dmg.sha256
```

### Linux

```bash
# Install tools
sudo apt-get install appimage-builder dpkg-dev

# Build executable
pyinstaller --name "PhoenixDrive" \
  --onefile \
  --windowed \
  --icon assets/images/icon.png \
  main_enhanced.py

# Create AppImage
appimage-builder --recipe AppImageBuilder.yml

# Create DEB package
mkdir -p debian/phoenixdrive/usr/bin
cp dist/PhoenixDrive debian/phoenixdrive/usr/bin/
dpkg-deb --build debian/phoenixdrive
mv debian/phoenixdrive.deb dist/phoenixdrive_2.0.0_amd64.deb

# Generate checksums
sha256sum dist/PhoenixDrive-2.0.0.AppImage > dist/PhoenixDrive-2.0.0.AppImage.sha256
sha256sum dist/phoenixdrive_2.0.0_amd64.deb > dist/phoenixdrive_2.0.0_amd64.deb.sha256
```

### Create GitHub Release

```bash
# Install GitHub CLI
# macOS: brew install gh
# Linux: sudo apt-get install gh
# Windows: choco install gh

# Login to GitHub
gh auth login

# Create release
gh release create v2.0.0 \
  --title "PhoenixDrive 2.0.0" \
  --notes "Release notes here"

# Upload Windows
gh release upload v2.0.0 dist/PhoenixDrive-Setup-2.0.0.exe
gh release upload v2.0.0 dist/PhoenixDrive-Setup-2.0.0.exe.sha256

# Upload macOS
gh release upload v2.0.0 dist/PhoenixDrive-2.0.0.dmg
gh release upload v2.0.0 dist/PhoenixDrive-2.0.0.dmg.sha256

# Upload Linux
gh release upload v2.0.0 dist/PhoenixDrive-2.0.0.AppImage
gh release upload v2.0.0 dist/PhoenixDrive-2.0.0.AppImage.sha256
gh release upload v2.0.0 dist/phoenixdrive_2.0.0_amd64.deb
gh release upload v2.0.0 dist/phoenixdrive_2.0.0_amd64.deb.sha256
```

---

## Mobile App Building

### iOS

```bash
# Navigate to project
cd /home/ubuntu/phoenix-core-mobile

# Build for iOS (with auto-submit to TestFlight)
eas build --platform ios --auto-submit

# Or without auto-submit
eas build --platform ios

# Monitor build
eas build:view

# Submit to App Store (manual)
eas submit --platform ios
```

### Android

```bash
# Navigate to project
cd /home/ubuntu/phoenix-core-mobile

# Build for Android (with auto-submit to Play Store)
eas build --platform android --auto-submit

# Or without auto-submit
eas build --platform android

# Monitor build
eas build:view

# Submit to Play Store (manual)
eas submit --platform android
```

### Both Platforms

```bash
# Build for both iOS and Android
eas build --platform all

# Build and submit both
eas build --platform all --auto-submit
```

---

## Environment Configuration

### Set Vercel Environment Variables

```bash
# Set individual variables
vercel env add SUPABASE_URL "https://your-project.supabase.co"
vercel env add SUPABASE_KEY "your-key"
vercel env add DATABASE_URL "postgresql://..."
vercel env add JWT_SECRET "your-secret"
vercel env add CORS_ORIGINS "https://your-app.com"

# Pull variables locally
vercel env pull

# Redeploy with new variables
vercel --prod
```

### Update Mobile App Config

```bash
# Edit app.config.ts
nano app.config.ts

# Update API URLs
# apiUrl: "https://phoenix-drive-api.vercel.app"
# wsUrl: "wss://phoenix-drive-api.vercel.app"

# Rebuild mobile apps
eas build --platform all
```

---

## Testing & Verification

### Test Backend

```bash
# Health check
curl https://phoenix-drive-api.vercel.app/api/v1/health

# Database status
curl https://phoenix-drive-api.vercel.app/api/v1/database/status

# API documentation
curl https://phoenix-drive-api.vercel.app/docs

# WebSocket test
wscat -c wss://phoenix-drive-api.vercel.app/socket.io
```

### Test Desktop App

```bash
# Windows
PhoenixDrive-Setup-2.0.0.exe

# macOS
open dist/PhoenixDrive-2.0.0.dmg

# Linux AppImage
chmod +x PhoenixDrive-2.0.0.AppImage
./PhoenixDrive-2.0.0.AppImage

# Linux DEB
sudo dpkg -i phoenixdrive_2.0.0_amd64.deb
phoenixdrive
```

### Verify Checksums

```bash
# Windows
sha256sum -c PhoenixDrive-Setup-2.0.0.exe.sha256

# macOS
sha256sum -c PhoenixDrive-2.0.0.dmg.sha256

# Linux
sha256sum -c PhoenixDrive-2.0.0.AppImage.sha256
sha256sum -c phoenixdrive_2.0.0_amd64.deb.sha256
```

---

## Monitoring & Logs

### Vercel

```bash
# View deployment logs
vercel logs

# View real-time logs
vercel logs --follow

# View specific deployment
vercel logs --id <DEPLOYMENT_ID>
```

### Supabase

```bash
# View database logs (via CLI)
# Install: npm install -g supabase
supabase logs --project-ref your-project

# Or via dashboard
# https://app.supabase.com/project/your-project/logs
```

### Sentry

```bash
# View error logs
# https://sentry.io/organizations/your-org/issues/

# Set up alerts
# https://sentry.io/settings/your-org/alerts/
```

### Datadog

```bash
# View metrics
# https://app.datadoghq.com/dashboard/

# View logs
# https://app.datadoghq.com/logs
```

---

## Rollback Procedures

### Vercel Rollback

```bash
# View deployment history
vercel list

# Rollback to previous deployment
vercel rollback

# Or redeploy specific commit
vercel --prod
```

### Database Rollback

```bash
# Via Supabase dashboard
# https://app.supabase.com/project/your-project/backups

# Or via CLI
supabase db pull  # Get latest schema
supabase db reset  # Reset database
```

---

## Common Issues & Fixes

### Vercel Deployment Fails

```bash
# Check logs
vercel logs

# Pull environment
vercel env pull

# Rebuild
vercel --prod --force
```

### Database Connection Error

```bash
# Test connection
psql $DATABASE_URL -c "SELECT 1"

# Check IP whitelist in Supabase
# https://app.supabase.com/project/your-project/settings/database

# Verify DATABASE_URL format
echo $DATABASE_URL
```

### Build Fails

```bash
# Clear cache
rm -rf build dist *.spec

# Rebuild with verbose output
pyinstaller --debug=all main_enhanced.py
```

### WebSocket Not Working

```bash
# Test WebSocket
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
  https://phoenix-drive-api.vercel.app/socket.io

# Check CORS
curl -H "Origin: https://your-app.com" \
  https://phoenix-drive-api.vercel.app/api/v1/health
```

---

## Useful Links

- **Vercel Dashboard:** https://vercel.com/dashboard
- **Supabase Dashboard:** https://app.supabase.com
- **App Store Connect:** https://appstoreconnect.apple.com
- **Google Play Console:** https://play.google.com/console
- **GitHub Repository:** https://github.com/Bboy9090/PhoenixCore-
- **Sentry Dashboard:** https://sentry.io/dashboard
- **Datadog Dashboard:** https://app.datadoghq.com

---

## Quick Deployment Checklist

### Before Deployment
- [ ] All code committed to Git
- [ ] Environment variables configured
- [ ] Tests passing
- [ ] Version number updated

### Deploy Backend
- [ ] Run `./deploy-vercel-automated.sh`
- [ ] Verify health endpoint
- [ ] Check database connection
- [ ] Monitor logs

### Build Desktop App
- [ ] Build for Windows/macOS/Linux
- [ ] Sign executables
- [ ] Create installers
- [ ] Generate checksums
- [ ] Create GitHub release

### Deploy Mobile Apps
- [ ] Build iOS: `eas build --platform ios`
- [ ] Build Android: `eas build --platform android`
- [ ] Test on devices
- [ ] Submit to App Stores

### Post-Deployment
- [ ] Monitor error rates
- [ ] Check user feedback
- [ ] Monitor performance
- [ ] Plan next release

---

**Last Updated:** May 5, 2026  
**Status:** ✅ Ready to Deploy
