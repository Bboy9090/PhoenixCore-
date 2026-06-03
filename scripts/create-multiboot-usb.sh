#!/bin/bash
# scripts/create-multiboot-usb.sh - Native macOS tool to create a branded Blue Phoenix Multi-Boot USB for Intel Macs
set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ISO_DIR="$REPO_ROOT/iso/outputs"

echo "=========================================================="
echo "🛡️  Blue Phoenix OS: Master Multi-Boot USB Creator (macOS)"
echo "=========================================================="
echo "This script formats a USB drive, installs our custom UEFI GRUB"
echo "loader extracted from our builds, and copies all active boot artifacts"
echo "to allow you to multi-boot any edition on your iMac 2015."
echo "=========================================================="
echo ""

# 1. Check if boot artifacts exist
ARTIFACTS=()
while IFS= read -r -d '' artifact; do
    case "$(basename "$artifact")" in
        bwos-home.iso|bwos-aurelia.iso|bwos-arcwyre.iso|bwos-thunder-god.iso)
            ARTIFACTS+=("$artifact")
            ;;
        *)
            continue
            ;;
    esac
done < <(find "$ISO_DIR" -maxdepth 1 \( -name "*.iso" -o -name "*.img" \) -print0)
if [ ${#ARTIFACTS[@]} -eq 0 ]; then
    echo "❌ Error: No compiled boot artifacts found in $ISO_DIR."
    echo "   Please run the relevant build matrix first."
    exit 1
fi

echo "Found ${#ARTIFACTS[@]} compiled boot artifacts to load."
echo ""

# 2. List available disks
echo "Listing connected storage devices:"
diskutil list external
echo ""

read -p "🔌 Enter the target USB disk identifier (e.g., disk12): " TARGET_DISK
TARGET_DISK="${TARGET_DISK#/dev/}"
if [ -z "$TARGET_DISK" ]; then
    echo "❌ Disk identifier cannot be empty."
    exit 1
fi

# Confirm disk exists
if ! diskutil info "$TARGET_DISK" >/dev/null 2>&1; then
    echo "❌ Error: Disk '/dev/$TARGET_DISK' not found."
    exit 1
fi

echo ""
echo "⚠️  WARNING: ALL DATA ON /dev/$TARGET_DISK WILL BE COMPLETELY DESTROYED!"
echo "Double-check your disk identifier! You selected:"
diskutil info "$TARGET_DISK" | grep -E "Device Identifier|Device / Media Name|Total Size"
echo ""

read -p "🔥 Are you absolutely sure you want to proceed? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "❌ Aborted."
    exit 0
fi

# 3. Partitioning the USB
echo ""
echo "🧹 Partitioning /dev/$TARGET_DISK..."
# Partition map GPT with 1 partition. macOS automatically creates the EFI system partition (s1)
# and formats our requested partition as s2.
diskutil partitionDisk "$TARGET_DISK" 1 GPT exFAT "BluePhoenix" R

echo "✅ Partitioning complete."
echo ""

EFI_PART="${TARGET_DISK}s1"
DATA_PART="${TARGET_DISK}s2"

# 4. Format and mount partitions
echo "Formatting EFI partition as FAT32..."
diskutil eraseVolume "MS-DOS FAT32" "EFI" "/dev/$EFI_PART"

# macOS sometimes renumbers the slice during eraseVolume
EFI_PART=$(diskutil list "/dev/$TARGET_DISK" | grep -i "EFI" | awk '{print $NF}')
if [ -z "$EFI_PART" ]; then
    EFI_PART="${TARGET_DISK}s1" # fallback
fi

echo "Mounting partitions..."
diskutil mount "/dev/$EFI_PART" || true
diskutil mount "/dev/$DATA_PART" || true

# Get mount paths
EFI_MOUNT=$(diskutil info "$EFI_PART" | grep "Mount Point" | sed 's/.*Mount Point:[[:space:]]*//')
DATA_MOUNT=$(diskutil info "$DATA_PART" | grep "Mount Point" | sed 's/.*Mount Point:[[:space:]]*//')

echo "EFI Partition Mount: $EFI_MOUNT"
echo "Data Partition Mount: $DATA_MOUNT"
echo ""

# 5. Extract Bootloader from compiled boot artifact
FIRST_ARTIFACT="${ARTIFACTS[0]}"
echo "📀 Extracting EFI bootloader from $(basename "$FIRST_ARTIFACT")..."
TEMP_MOUNT="/tmp/bp_iso_mount"
mkdir -p "$TEMP_MOUNT"

# Mount boot artifact read-only
hdiutil attach -nomount "$FIRST_ARTIFACT" -noverify
# Find the boot artifact disk mount node
ISO_NODE=$(diskutil list | grep "PHOENIX_OS" | awk '{print $NF}' | head -n 1)
if [ -z "$ISO_NODE" ]; then
    # Try alternate mount identification
    ISO_NODE=$(diskutil list | grep -B 2 "CD_partition_scheme" | head -n 1 | awk '{print $1}')
fi

mount -t cd9660 "/dev/$ISO_NODE" "$TEMP_MOUNT"

echo "Copying UEFI GRUB system files to EFI partition..."
mkdir -p "$EFI_MOUNT/EFI/BOOT"
mkdir -p "$EFI_MOUNT/boot/grub"

# Copy GRUB boot binaries and themes
cp -R "$TEMP_MOUNT/boot/" "$EFI_MOUNT/boot/"
cp -R "$TEMP_MOUNT/EFI/" "$EFI_MOUNT/EFI/"

# Unmount ISO
umount "$TEMP_MOUNT" || true
hdiutil detach "/dev/$(echo "$ISO_NODE" | cut -d's' -f1)" || true
rm -rf "$TEMP_MOUNT"

echo "✅ Bootloader extraction complete."
echo ""

# 6. Copying boot artifacts to Data Partition
echo "📦 Copying boot artifacts to Data Partition (this may take several minutes, please wait)..."
mkdir -p "$DATA_MOUNT/boot/iso"
for artifact in "${ARTIFACTS[@]}"; do
    if [ -f "$artifact" ]; then
        echo "  -> Copying $(basename "$artifact")..."
        cp "$artifact" "$DATA_MOUNT/boot/iso/" || echo "⚠️ Warning: Failed to copy $(basename "$artifact")"
    else
        echo "⚠️ Skipping missing artifact: $(basename "$artifact")"
    fi
done

echo "✅ All active boot artifacts copied."
echo ""

# 7. Write Custom GRUB Config
echo "✍️  Writing custom multi-boot grub.cfg..."

cat <<'EOF' > "$EFI_MOUNT/boot/grub/grub.cfg"
# Custom Blue Phoenix Multi-Boot grub.cfg for Intel Macs
set timeout=15
set default=0

# Style/Visuals
insmod part_gpt
insmod part_msdos
insmod ext2
insmod fat
insmod exfat

# Main Colors
menu_color_normal=white/black
menu_color_highlight=cyan/dark-gray

submenu "Blue Phoenix OS: Active Edition Boot Room" {

    menuentry "🏡 Blue Phoenix: Home Edition (Sky Blue)" --class os {
        set isofile="/boot/iso/bwos-home.iso"
        search --no-floppy --set=root --file $isofile
        loopback loop $isofile
        linux (loop)/live/vmlinuz boot=live findiso=$isofile components locales=en_US.UTF-8 quiet splash
        initrd (loop)/live/initrd.img
    }

    menuentry "🏡 Blue Phoenix: Home Legacy i386 (Boot Image)" --class os {
        set isofile="/boot/iso/bwos-home-legacy-i386.img"
        search --no-floppy --set=root --file $isofile
        loopback loop $isofile
        linux (loop)/live/vmlinuz boot=live findiso=$isofile components locales=en_US.UTF-8 quiet splash
        initrd (loop)/live/initrd.img
    }

    menuentry "👑 Blue Phoenix: Aurelia Edition (Gold)" --class os {
        set isofile="/boot/iso/bwos-aurelia.iso"
        search --no-floppy --set=root --file $isofile
        loopback loop $isofile
        linux (loop)/live/vmlinuz boot=live findiso=$isofile components locales=en_US.UTF-8 quiet splash
        initrd (loop)/live/initrd.img
    }

    menuentry "⚡ Arcwyre: Thundergod Edition (Electric Blue & Violet)" --class os {
        set isofile="/boot/iso/bwos-thunder-god.iso"
        search --no-floppy --set=root --file $isofile
        loopback loop $isofile
        linux (loop)/live/vmlinuz boot=live findiso=$isofile components locales=en_US.UTF-8 quiet splash
        initrd (loop)/live/initrd.img
    }

    menuentry "🛡️ Bobby’s Worldwide OS: ARCWYRE Edition (Cyber Recovery)" --class os {
        set isofile="/boot/iso/bwos-arcwyre.iso"
        search --no-floppy --set=root --file $isofile
        loopback loop $isofile
        linux (loop)/live/vmlinuz boot=live findiso=$isofile components locales=en_US.UTF-8 quiet splash
        initrd (loop)/live/initrd.img
    }

}
EOF

echo "✅ Custom grub.cfg written."
echo ""

# 8. Clean up
echo "🔌 Unmounting partitions..."
diskutil unmountDisk "/dev/$TARGET_DISK"

echo "=========================================================="
echo "🎉 SUCCESS: YOUR BLUE PHOENIX MULTI-BOOT USB IS READY!"
echo "=========================================================="
echo "To boot this USB on your iMac 2015:"
echo "1. Plug the USB into your iMac."
echo "2. Hold down the [Option / Alt] key and power it on."
echo "3. Choose the EFI Boot option."
echo "4. Welcome to the Active Edition Boot Room!"
echo "=========================================================="
