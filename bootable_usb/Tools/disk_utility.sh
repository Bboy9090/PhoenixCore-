#!/bin/bash
echo "BootForge Disk Utility"
echo "==================="
echo "1. List all disks"
echo "2. Check disk health"
echo "3. Mount disk"
echo "4. Unmount disk"
echo "5. Exit"
read -p "Choose option: " choice

case $choice in
    1) diskutil list ;;
    2) diskutil verifyVolume / ;;
    3) read -p "Enter disk identifier: " disk; diskutil mount $disk ;;
    4) read -p "Enter disk identifier: " disk; diskutil unmount $disk ;;
    5) exit ;;
esac
