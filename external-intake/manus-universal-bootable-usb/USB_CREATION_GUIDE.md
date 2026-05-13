# Phoenix OS USB Creation Guide

This guide explains how to create a bootable Phoenix OS USB drive from the ISO image and test it on your external SSD.

---

## Prerequisites

- **Phoenix OS ISO** (downloaded or built)
- **USB Drive** (8GB+ recommended)
- **External SSD** (for testing the installation)
- **Disk utility software** (varies by OS)

---

## Step 1: Download or Build Phoenix OS ISO

### Option A: Download Pre-built ISO

```bash
# Download from GitHub Releases
wget https://github.com/Bboy9090/phoenixcore/releases/download/v2.0.0/phoenix-os-2.0.0-amd64.iso
```

### Option B: Build Locally

On your local machine with sufficient disk space (50GB+):

```bash
# Clone repository
git clone https://github.com/Bboy9090/phoenixcore.git
cd phoenixcore/apps/os

# Install dependencies
sudo apt-get install live-build debootstrap squashfs-tools xorriso

# Build ISO
sudo bash scripts/build-iso.sh

# ISO will be in: dist/phoenix-os-2.0.0-amd64.iso
```

---

## Step 2: Prepare USB Drive

### On Linux

**1. Identify USB device:**
```bash
lsblk
# Look for your USB drive (e.g., /dev/sdb)
```

**2. Unmount USB (if mounted):**
```bash
sudo umount /dev/sdb*
```

**3. Write ISO to USB:**
```bash
# Using dd (direct disk dump)
sudo dd if=phoenix-os-2.0.0-amd64.iso of=/dev/sdb bs=4M status=progress
sudo sync

# Or using Etcher (GUI)
sudo apt-get install balena-etcher-electron
# Open Etcher, select ISO, select USB, flash
```

**4. Eject USB:**
```bash
sudo eject /dev/sdb
```

### On macOS

**1. Identify USB device:**
```bash
diskutil list
# Look for your USB drive (e.g., /dev/disk2)
```

**2. Unmount USB:**
```bash
diskutil unmountDisk /dev/disk2
```

**3. Write ISO to USB:**
```bash
# Using dd
sudo dd if=phoenix-os-2.0.0-amd64.iso of=/dev/rdisk2 bs=4m
sudo sync

# Or using Etcher
# Download from https://www.balena.io/etcher/
```

**4. Eject USB:**
```bash
diskutil eject /dev/disk2
```

### On Windows

**1. Download Balena Etcher:**
   - Visit https://www.balena.io/etcher/
   - Download and install

**2. Open Etcher and:**
   - Click "Select image" → Choose `phoenix-os-2.0.0-amd64.iso`
   - Click "Select target" → Choose your USB drive
   - Click "Flash"
   - Wait for completion

**3. Eject USB safely**

---

## Step 3: Boot from USB

### BIOS/UEFI Settings

1. **Insert USB drive** into your computer
2. **Restart computer**
3. **Enter BIOS/UEFI** (usually F2, F12, Del, or Esc during boot)
4. **Set boot order:**
   - Move USB to first position
   - Save and exit
5. **Computer will boot from USB**

### Boot Menu (Alternative)

1. **Insert USB drive**
2. **Restart computer**
3. **Press boot menu key** (usually F12, F11, or Esc)
4. **Select USB drive** from menu
5. **Press Enter**

---

## Step 4: Test on External SSD

### Option A: Live Boot (No Installation)

1. Boot from USB
2. Select "Try Phoenix OS" or "Live Mode"
3. Test all features without installing
4. Eject USB to shut down

### Option B: Install to External SSD

**WARNING: This will erase the external SSD. Backup data first!**

1. Boot from USB
2. Select "Install Phoenix OS"
3. Follow Calamares installer:
   - Select language
   - Select timezone
   - Select keyboard layout
   - Select installation target: **Your external SSD** (e.g., `/dev/sdb`)
   - Confirm installation
   - Wait for completion
4. Remove USB drive
5. Restart computer
6. Boot from external SSD

### Option C: Persistent Live Boot

1. Boot from USB
2. Select "Live with persistence"
3. Changes are saved to USB
4. Useful for testing without full installation

---

## Step 5: Testing Checklist

### System Boot
- [ ] USB boots successfully
- [ ] Splash screen displays
- [ ] KDE Plasma loads
- [ ] Desktop is responsive

### Hardware Detection
- [ ] CPU info displays correctly
- [ ] Memory info displays correctly
- [ ] Disk info displays correctly
- [ ] GPU detected (if applicable)
- [ ] Network detected

### Applications
- [ ] Phoenix Control Center launches
- [ ] System monitoring works
- [ ] Disk tools accessible
- [ ] Recovery tools available
- [ ] Terminal works

### Performance
- [ ] Boot time < 30 seconds
- [ ] Application launch < 2 seconds
- [ ] No crashes or errors
- [ ] Smooth scrolling and animations

### Connectivity
- [ ] WiFi connects
- [ ] Ethernet connects
- [ ] Mobile app can connect to desktop app
- [ ] QR code scanning works

---

## Troubleshooting

### USB Won't Boot

**Solution 1:** Verify ISO was written correctly
```bash
# Check ISO integrity
sha256sum phoenix-os-2.0.0-amd64.iso
# Compare with official checksum
```

**Solution 2:** Try different USB port or USB drive

**Solution 3:** Disable Secure Boot in BIOS

**Solution 4:** Try UEFI mode instead of Legacy

### System Freezes During Boot

**Solution 1:** Add kernel parameters
- At boot menu, press 'e' to edit
- Add: `nomodeset` or `acpi=off`
- Press Ctrl+X to boot

**Solution 2:** Try different graphics mode
- At boot menu, select "Safe graphics mode"

### External SSD Not Detected

**Solution 1:** Check USB connection
- Try different USB port
- Try different USB cable

**Solution 2:** Check BIOS settings
- Ensure SATA/USB is enabled
- Try different SATA mode (AHCI)

**Solution 3:** Partition table issue
- Boot live, open GParted
- Recreate partition table if needed

### Installation Fails

**Solution 1:** Check disk space
- External SSD needs 20GB+ free space

**Solution 2:** Check disk health
```bash
# In live environment
sudo badblocks -v /dev/sdb
```

**Solution 3:** Try manual partitioning
- Use GParted to create partitions
- Then install to those partitions

---

## Performance Optimization

### For External SSD

1. **Enable TRIM:**
```bash
sudo systemctl enable fstrim.timer
```

2. **Optimize I/O:**
```bash
# Edit /etc/fstab, add 'noatime' option
/dev/sdb1 / ext4 defaults,noatime 0 1
```

3. **Disable journaling (optional):**
```bash
sudo tune2fs -O ^has_journal /dev/sdb1
```

### For Performance Testing

1. **Boot with profiling:**
```bash
# At boot menu, add: systemd.log_level=debug
```

2. **Check boot time:**
```bash
systemd-analyze
systemd-analyze blame
```

3. **Monitor resources:**
```bash
top
htop
iotop
```

---

## Next Steps

### After Successful Boot

1. **Test all features** using checklist above
2. **Report any issues** on GitHub
3. **Provide feedback** on Discord
4. **Help improve** Phoenix OS

### For Development

1. **Clone repository** on installed system
2. **Build custom packages**
3. **Test new features**
4. **Submit pull requests**

---

## Support Resources

- **GitHub Issues:** https://github.com/Bboy9090/phoenixcore/issues
- **Discord Community:** https://discord.gg/phoenixos
- **Documentation:** https://docs.phoenixos.dev
- **Wiki:** https://wiki.phoenixos.dev

---

## Safety Warnings

⚠️ **WARNING: Data Loss Risk**

- Writing to wrong disk can erase your data
- Always verify device name before writing
- Backup important data before testing
- Use external SSD to avoid damaging main system
- Never write to `/dev/sda` unless you know what you're doing

---

**Phoenix OS USB Creation Complete** ✅

Your bootable USB is ready for testing. Follow the steps above to boot and test Phoenix OS on your external SSD.

Phoenix OS — Professional Linux for System Recovery and Repair 🔥
