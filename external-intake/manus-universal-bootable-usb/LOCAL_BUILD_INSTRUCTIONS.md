# Local Phoenix OS Build Instructions

Since the sandbox environment has limited disk space (25GB), this guide explains how to build Phoenix OS on your local machine with sufficient resources.

---

## System Requirements

### Minimum
- **OS:** Ubuntu 22.04 LTS, Debian 12, or equivalent
- **CPU:** 4 cores (8+ recommended)
- **RAM:** 8GB (16GB+ recommended)
- **Disk Space:** 50GB free (for build)
- **Network:** Broadband internet connection

### Recommended
- **OS:** Ubuntu 22.04 LTS (latest)
- **CPU:** 8+ cores
- **RAM:** 16GB+
- **Disk Space:** 100GB free
- **Network:** Fast internet (build downloads ~3GB)

---

## Step 1: Install Build Dependencies

### Ubuntu/Debian

```bash
# Update package lists
sudo apt-get update

# Install live-build and dependencies
sudo apt-get install -y \
  live-build \
  debootstrap \
  squashfs-tools \
  xorriso \
  isolinux \
  syslinux-common \
  git \
  wget \
  curl

# Verify installation
live-build --version
debootstrap --version
xorriso --version
```

### Fedora/RHEL

```bash
# Install dependencies
sudo dnf install -y \
  live-media \
  debootstrap \
  squashfs-tools \
  libisoburn \
  syslinux \
  git \
  wget \
  curl
```

### Arch Linux

```bash
# Install dependencies
sudo pacman -S \
  live-media \
  debootstrap \
  squashfs-tools \
  libisoburn \
  syslinux \
  git \
  wget \
  curl
```

---

## Step 2: Clone Phoenix Repository

```bash
# Clone the repository
git clone https://github.com/Bboy9090/phoenixcore.git
cd phoenixcore/apps/os

# Verify structure
ls -la
# Should show: live-build/, installer/, scripts/, docs/, etc.
```

---

## Step 3: Prepare Build Environment

```bash
# Create build directory
mkdir -p build
cd build

# Copy live-build configuration
cp -r ../live-build/config .

# Verify configuration
ls -la config/
```

---

## Step 4: Run Build Script

### Option A: Automated Build (Recommended)

```bash
# From phoenixcore/apps/os directory
cd /path/to/phoenixcore/apps/os

# Run build script
sudo bash scripts/build-iso.sh

# This will:
# 1. Verify prerequisites
# 2. Configure live-build
# 3. Bootstrap Debian base system
# 4. Install packages
# 5. Install custom applications
# 6. Configure branding
# 7. Build ISO image
# 8. Generate checksums
# 9. Create dist/ directory with ISO
```

### Option B: Manual Build (Advanced)

```bash
cd build

# Initialize live-build
sudo lb config \
  --architecture amd64 \
  --distribution jammy \
  --archive-areas "main universe multiverse restricted" \
  --mirror-bootstrap http://archive.ubuntu.com/ubuntu/ \
  --mirror-chroot http://archive.ubuntu.com/ubuntu/ \
  --mirror-chroot-security http://security.ubuntu.com/ubuntu/ \
  --mirror-binary http://archive.ubuntu.com/ubuntu/ \
  --mirror-binary-security http://security.ubuntu.com/ubuntu/ \
  --debootstrap-options "--keyring=/usr/share/keyrings/ubuntu-archive-keyring.gpg" \
  --bootloader grub-efi \
  --image-type iso-hybrid

# Copy package lists
cp ../live-build/package-lists/*.list* config/package-lists/

# Build
sudo lb build

# ISO will be created as: live-image-amd64.iso
```

---

## Step 5: Monitor Build Progress

### During Build

```bash
# In another terminal, monitor disk usage
watch -n 5 df -h

# Monitor system resources
top
htop

# Check build logs
tail -f /var/log/live-build.log
```

### Build Time Estimates

| Stage | Time | Notes |
|-------|------|-------|
| Debootstrap | 5-10 min | Downloads base system |
| Package install | 15-30 min | Installs 500+ packages |
| Customization | 5-10 min | Applies branding/config |
| ISO creation | 10-15 min | Compresses filesystem |
| **Total** | **35-65 min** | Depends on internet speed |

---

## Step 6: Verify Build Output

```bash
# Check if build succeeded
ls -lh dist/
# Should show: phoenix-os-2.0.0-amd64.iso (~2-3GB)

# Verify ISO integrity
sha256sum dist/phoenix-os-2.0.0-amd64.iso
# Compare with official checksum from GitHub

# Check ISO contents
file dist/phoenix-os-2.0.0-amd64.iso
# Should show: "ISO 9660 CD-ROM filesystem data"

# Mount and inspect (optional)
mkdir -p /tmp/iso-mount
sudo mount -o loop dist/phoenix-os-2.0.0-amd64.iso /tmp/iso-mount
ls -la /tmp/iso-mount/
sudo umount /tmp/iso-mount
```

---

## Step 7: Create Bootable USB

See `USB_CREATION_GUIDE.md` for detailed instructions on:
- Writing ISO to USB drive
- Booting from USB
- Testing on external SSD

Quick command:
```bash
# Linux
sudo dd if=dist/phoenix-os-2.0.0-amd64.iso of=/dev/sdb bs=4M status=progress
sudo sync

# macOS
sudo dd if=dist/phoenix-os-2.0.0-amd64.iso of=/dev/rdisk2 bs=4m
sudo sync
```

---

## Troubleshooting

### Build Fails: "Not enough disk space"

**Solution:**
```bash
# Check available space
df -h

# Clean previous builds
sudo lb clean --all

# Use external drive
cd /mnt/external-drive
sudo lb build
```

### Build Fails: "Package not found"

**Solution:**
```bash
# Update package lists
sudo apt-get update

# Manually install missing package
sudo apt-get install <package-name>

# Retry build
sudo lb build
```

### Build Fails: "Network error"

**Solution:**
```bash
# Check internet connection
ping archive.ubuntu.com

# Try different mirror
# Edit config/archives/ubuntu.list.chroot
# Change mirror URL

# Retry build
sudo lb clean --all
sudo lb build
```

### Build Takes Too Long

**Solution:**
```bash
# Use faster mirror
# Edit config/archives/ubuntu.list.chroot
# Use local mirror if available

# Reduce package count
# Edit config/package-lists/desktop.list.chroot
# Remove unnecessary packages

# Use SSD for build
# Move build directory to SSD
# Significantly faster I/O
```

### ISO Won't Boot

**Solution:**
```bash
# Verify ISO integrity
sha256sum dist/phoenix-os-2.0.0-amd64.iso

# Try rebuilding with different bootloader
sudo lb config --bootloader syslinux
sudo lb build

# Test in virtual machine first
# Use VirtualBox or QEMU
qemu-system-x86_64 -cdrom dist/phoenix-os-2.0.0-amd64.iso -m 2048
```

---

## Advanced Options

### Customize Packages

Edit `live-build/package-lists/desktop.list.chroot`:

```bash
# Add packages
echo "package-name" >> config/package-lists/desktop.list.chroot

# Remove packages
sed -i '/^package-name$/d' config/package-lists/desktop.list.chroot

# Rebuild
sudo lb clean --all
sudo lb build
```

### Customize Branding

Edit `live-build/config/includes.chroot/`:

```bash
# Add custom wallpaper
cp /path/to/wallpaper.png config/includes.chroot/usr/share/backgrounds/

# Add custom boot splash
cp /path/to/splash.png config/includes.chroot/boot/

# Add custom theme
cp -r /path/to/theme config/includes.chroot/usr/share/themes/

# Rebuild
sudo lb build
```

### Add Custom Scripts

Create `live-build/config/hooks/normal/`:

```bash
# Create hook script
cat > config/hooks/normal/99-custom.chroot << 'EOF'
#!/bin/bash
# Custom post-installation script
echo "Running custom configuration..."

# Your commands here
apt-get install -y custom-package
systemctl enable custom-service

echo "Custom configuration complete"
EOF

# Make executable
chmod +x config/hooks/normal/99-custom.chroot

# Rebuild
sudo lb build
```

---

## Performance Optimization

### Faster Builds

```bash
# Use tmpfs for faster I/O
sudo mount -t tmpfs -o size=30G tmpfs /mnt/build
cd /mnt/build
sudo lb build

# Use parallel processing
export MAKEFLAGS="-j$(nproc)"
sudo lb build
```

### Smaller ISO

```bash
# Remove unnecessary packages
# Edit config/package-lists/desktop.list.chroot
# Remove: kde-full, games, office-suite, etc.

# Remove documentation
# Add to config/hooks/normal/99-cleanup.chroot
find /usr/share/doc -type f -delete
find /usr/share/man -type f -delete

# Compress more aggressively
sudo lb config --compression bzip2
```

### Faster Boot

```bash
# Add to config/includes.chroot/etc/default/grub
GRUB_CMDLINE_LINUX="quiet splash elevator=noop"

# Disable unnecessary services
systemctl disable bluetooth
systemctl disable cups
systemctl disable avahi-daemon
```

---

## Next Steps

1. **Build ISO** — Follow steps above
2. **Create USB** — See USB_CREATION_GUIDE.md
3. **Test on External SSD** — Boot and verify
4. **Report Issues** — GitHub Issues
5. **Contribute** — Submit improvements

---

## Support

- **Build Issues:** https://github.com/Bboy9090/phoenixcore/issues
- **Live-build Docs:** https://live-team.pages.debian.net/live-manual/
- **Discord:** https://discord.gg/phoenixos

---

**Phoenix OS Local Build Complete** ✅

Your ISO is ready for testing. Follow USB_CREATION_GUIDE.md to create a bootable USB and test on your external SSD.

Phoenix OS — Professional Linux for System Recovery and Repair 🔥
