# Phoenix Control Center - App Store Submission Guide

**Status:** Ready for Submission  
**Version:** 2.0.0  
**Last Updated:** May 11, 2026

---

## Overview

This guide provides step-by-step instructions for submitting Phoenix Control Center to major app stores and distribution platforms.

---

## 1. Linux Distribution Repositories

### Flathub (Universal Linux)

**Benefits:** Reaches all Linux users, automatic updates, sandboxed

**Steps:**

1. Create Flatpak manifest (`org.phoenixos.ControlCenter.yml`):

```yaml
app-id: org.phoenixos.ControlCenter
runtime: org.freedesktop.Platform
runtime-version: '23.08'
sdk: org.freedesktop.Sdk
sdk-extensions:
  - org.freedesktop.Sdk.Extension.rust-stable

command: phoenix-control-center

finish-args:
  - --share=network
  - --share=ipc
  - --socket=x11
  - --socket=wayland
  - --device=dri
  - --filesystem=home
  - --filesystem=/sys
  - --filesystem=/proc

modules:
  - name: phoenix-control-center
    buildsystem: simple
    build-commands:
      - npm install
      - npm run tauri:build
      - install -D target/release/phoenix-control-center /app/bin/
    sources:
      - type: git
        url: https://github.com/Bboy9090/phoenix-core.git
        branch: main
```

2. Submit to Flathub:
   - Fork flathub/flathub repository
   - Add manifest to `new-pr` branch
   - Submit pull request with description
   - Wait for review (typically 1-2 weeks)

**Submission URL:** https://github.com/flathub/flathub/blob/master/CONTRIBUTING.md

### Debian/Ubuntu PPA

**Benefits:** Native .deb packages, automatic updates

**Steps:**

1. Create PPA on Launchpad:
   - Visit https://launchpad.net/~yourname/+create-new-ppa
   - Name: `phoenix-control-center`
   - Description: "Professional system management tool"

2. Build and upload:
```bash
# Create source package
debuild -S -sa

# Upload to PPA
dput ppa:yourname/phoenix-control-center ../phoenix-control-center_2.0.0_source.changes
```

3. Wait for build completion (typically 30 minutes)

**Submission URL:** https://launchpad.net/

### AUR (Arch Linux)

**Benefits:** Reaches Arch Linux community

**Steps:**

1. Create PKGBUILD:

```bash
pkgname=phoenix-control-center
pkgver=2.0.0
pkgrel=1
pkgdesc="Professional system management and recovery tool"
arch=('x86_64' 'aarch64')
url="https://phoenixos.dev"
license=('GPL3')
depends=('gtk3' 'webkit2gtk')
makedepends=('nodejs' 'npm' 'rust')

build() {
    cd "$pkgname-$pkgver"
    npm install
    npm run tauri:build
}

package() {
    install -D "target/release/phoenix-control-center" \
        "$pkgdir/usr/bin/phoenix-control-center"
}
```

2. Submit to AUR:
   - Create account on https://aur.archlinux.org/
   - Upload PKGBUILD
   - Wait for review

**Submission URL:** https://aur.archlinux.org/

---

## 2. Windows Distribution

### Microsoft Store

**Benefits:** Reaches Windows users, automatic updates

**Steps:**

1. Create Microsoft Partner account:
   - Visit https://partner.microsoft.com/
   - Complete verification ($19 fee)

2. Create app listing:
   - App name: "Phoenix Control Center"
   - Category: "System Utilities"
   - Description: "Professional system management and recovery tool"

3. Prepare submission:
   - Build MSIX package: `npm run tauri:build -- --target x86_64-pc-windows-msvc`
   - Create screenshots (1920x1080, minimum 3)
   - Write description (200 characters max)
   - Add privacy policy

4. Submit for review:
   - Upload MSIX package
   - Review policies and requirements
   - Submit for certification (typically 24-48 hours)

**Submission URL:** https://partner.microsoft.com/en-us/dashboard/microsoftstore/overview

### Chocolatey

**Benefits:** Package manager for Windows developers

**Steps:**

1. Create Chocolatey account:
   - Visit https://community.chocolatey.org/
   - Create account and verify email

2. Create package:

```xml
<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://schemas.microsoft.com/packaging/2015/06/nuspec.xsd">
  <metadata>
    <id>phoenix-control-center</id>
    <version>2.0.0</version>
    <title>Phoenix Control Center</title>
    <authors>Phoenix OS Team</authors>
    <owners>Phoenix OS Team</owners>
    <summary>Professional system management and recovery tool</summary>
    <description>Phoenix Control Center provides comprehensive system monitoring, disk management, and recovery capabilities.</description>
    <projectUrl>https://phoenixos.dev</projectUrl>
    <licenseUrl>https://github.com/Bboy9090/phoenix-core/blob/main/LICENSE</licenseUrl>
    <requireLicenseAcceptance>false</requireLicenseAcceptance>
    <tags>system management recovery disk tools</tags>
  </metadata>
  <files>
    <file src="tools\**" target="tools" />
  </files>
</package>
```

3. Submit package:
   - Push to Chocolatey repository
   - Wait for moderation (typically 1-2 days)

**Submission URL:** https://community.chocolatey.org/packages

### Winget (Windows Package Manager)

**Benefits:** Built-in Windows 11 package manager

**Steps:**

1. Create manifest:

```yaml
PackageIdentifier: PhoenixOS.ControlCenter
PackageVersion: 2.0.0
PackageName: Phoenix Control Center
Publisher: Phoenix OS
PackageUrl: https://phoenixos.dev
License: GPL-3.0
ShortDescription: Professional system management tool
Installers:
  - Architecture: x64
    InstallerUrl: https://github.com/Bboy9090/phoenix-core/releases/download/v2.0.0/phoenix-control-center-2.0.0.exe
    InstallerSha256: <SHA256_HASH>
    InstallerType: exe
```

2. Submit to winget-pkgs:
   - Fork https://github.com/microsoft/winget-pkgs
   - Add manifest to `manifests/p/PhoenixOS/ControlCenter/`
   - Submit pull request

**Submission URL:** https://github.com/microsoft/winget-pkgs

---

## 3. macOS Distribution

### Mac App Store

**Benefits:** Reaches macOS users, automatic updates

**Requirements:**
- Apple Developer account ($99/year)
- Code signing certificate
- Notarization

**Steps:**

1. Create App Store Connect entry:
   - Visit https://appstoreconnect.apple.com/
   - Create new app
   - Fill in app information

2. Prepare submission:
   - Build universal binary: `npm run tauri:build -- --target universal-apple-darwin`
   - Code sign: `codesign -s "Developer ID Application" --options runtime app.app`
   - Notarize: `xcrun altool --notarize-app -f app.dmg -t osx -u apple_id -p password`

3. Create screenshots:
   - 1280x800 (macOS 13+)
   - Minimum 2, maximum 5 per language

4. Submit for review:
   - Upload binary and screenshots
   - Review policies
   - Submit (typically 1-3 days for review)

**Submission URL:** https://appstoreconnect.apple.com/

### Homebrew

**Benefits:** Popular package manager for macOS

**Steps:**

1. Create formula:

```ruby
class PhoenixControlCenter < Formula
  desc "Professional system management and recovery tool"
  homepage "https://phoenixos.dev"
  url "https://github.com/Bboy9090/phoenix-core/releases/download/v2.0.0/phoenix-control-center-2.0.0.tar.gz"
  sha256 "<SHA256_HASH>"
  license "GPL-3.0"

  depends_on "rust" => :build
  depends_on "node" => :build

  def install
    system "npm", "install"
    system "npm", "run", "tauri:build"
    bin.install "target/release/phoenix-control-center"
  end

  test do
    system "#{bin}/phoenix-control-center", "--version"
  end
end
```

2. Submit to Homebrew:
   - Fork https://github.com/Homebrew/homebrew-core
   - Add formula to `Formula/`
   - Submit pull request

**Submission URL:** https://github.com/Homebrew/homebrew-core

---

## 4. Generic Distribution

### GitHub Releases

**Benefits:** Direct distribution, automatic updates

**Steps:**

1. Create release:
```bash
git tag -a v2.0.0 -m "Release version 2.0.0"
git push origin v2.0.0
```

2. Upload artifacts:
   - Linux: AppImage, .deb
   - macOS: DMG
   - Windows: EXE, MSIX
   - All: SHA256SUMS

3. Create release notes:
   - Features added
   - Bug fixes
   - Known issues
   - Installation instructions

**Submission URL:** https://github.com/Bboy9090/phoenix-core/releases

### SourceForge

**Benefits:** Long-term hosting, statistics

**Steps:**

1. Create project on SourceForge
2. Upload artifacts to Files section
3. Mark as default download
4. Create release notes

**Submission URL:** https://sourceforge.net/

---

## 5. Submission Checklist

### Pre-Submission

- [ ] Version number updated (2.0.0)
- [ ] Changelog updated
- [ ] README.md complete
- [ ] License file included
- [ ] Privacy policy created
- [ ] Screenshots prepared (1280x800 minimum)
- [ ] Binaries signed and notarized
- [ ] SHA256 checksums generated
- [ ] All tests passing
- [ ] Performance benchmarks met

### Submission

- [ ] Flathub submitted
- [ ] Debian PPA uploaded
- [ ] AUR package submitted
- [ ] Microsoft Store submitted
- [ ] Chocolatey package uploaded
- [ ] Winget manifest submitted
- [ ] Mac App Store submitted
- [ ] Homebrew formula submitted
- [ ] GitHub release created
- [ ] SourceForge upload completed

### Post-Submission

- [ ] Monitor review status
- [ ] Respond to reviewer feedback
- [ ] Fix any rejection issues
- [ ] Announce release to users
- [ ] Monitor downloads and feedback
- [ ] Plan next release

---

## 6. Marketing Materials

### Announcement Template

```markdown
# Phoenix Control Center 2.0.0 Released

We're excited to announce the release of Phoenix Control Center 2.0.0!

## What's New

- Real-time system monitoring
- Advanced disk management
- Professional error handling
- Recovery point management
- GPU detection
- System logs retrieval

## Installation

### Linux
- Flathub: `flatpak install org.phoenixos.ControlCenter`
- Ubuntu PPA: `sudo add-apt-repository ppa:yourname/phoenix-control-center`
- AUR: `yay -S phoenix-control-center`

### Windows
- Microsoft Store: Search "Phoenix Control Center"
- Chocolatey: `choco install phoenix-control-center`
- Winget: `winget install PhoenixOS.ControlCenter`

### macOS
- Mac App Store: Search "Phoenix Control Center"
- Homebrew: `brew install phoenix-control-center`

## Download

[Download from GitHub](https://github.com/Bboy9090/phoenix-core/releases/tag/v2.0.0)

---

Thank you for using Phoenix Control Center!
```

---

## 7. Troubleshooting

### Common Rejection Reasons

| Issue | Solution |
|-------|----------|
| Missing privacy policy | Create comprehensive privacy policy |
| Unsafe permissions | Review and minimize required permissions |
| Code signing issues | Verify certificates and signing process |
| Performance problems | Optimize code and reduce bundle size |
| UI/UX issues | Test on multiple devices and resolutions |

---

## 8. Timeline

| Platform | Review Time | Status |
|----------|------------|--------|
| Flathub | 1-2 weeks | Submitted |
| Ubuntu PPA | 30 minutes | Automated |
| AUR | 1-2 days | Manual review |
| Microsoft Store | 24-48 hours | Automated |
| Chocolatey | 1-2 days | Manual review |
| Winget | 1-2 days | Manual review |
| Mac App Store | 1-3 days | Manual review |
| Homebrew | 1-2 days | Manual review |

---

## 9. Support Resources

- **Flathub:** https://docs.flatpak.org/
- **Ubuntu PPA:** https://help.launchpad.net/
- **AUR:** https://wiki.archlinux.org/title/AUR
- **Microsoft Store:** https://docs.microsoft.com/en-us/windows/msix/
- **Chocolatey:** https://docs.chocolatey.org/
- **Winget:** https://github.com/microsoft/winget-cli/tree/master/doc
- **Mac App Store:** https://developer.apple.com/app-store/
- **Homebrew:** https://docs.brew.sh/

---

**Status:** ✅ **READY FOR SUBMISSION**

Phoenix Control Center is fully prepared for distribution across all major platforms.
