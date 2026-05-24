# Bobby's PhoenixDrive — End-to-End Testing Guide

## Overview

This guide provides step-by-step instructions for testing the complete workflow:
**Mobile App → Backend API → Desktop Consumer → USB Build**

---

## Prerequisites

1. **Backend API running** — Flask server wrapping PhoenixCore modules
2. **Mobile app running** — React Native Expo app
3. **Desktop Consumer ready** — Python CLI tool for building USBs
4. **Test USB drive** — At least 4GB USB drive (data will be erased)
5. **PhoenixCore repo** — Available at `/home/ubuntu/PhoenixCore-`

---

## Test Environment Setup

### 1. Start Backend API Server

```bash
cd /home/ubuntu/phoenix-core-mobile/server

# Install dependencies (if not already done)
pip install -r requirements.txt

# Start the API server
python api.py
```

**Expected Output:**
```
 * Running on http://127.0.0.1:5000
 * Press CTRL+C to quit
```

**Verify API is running:**
```bash
curl http://localhost:5000/api/v1/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-03-22T16:30:00Z"
}
```

### 2. Start Mobile App

```bash
cd /home/ubuntu/phoenix-core-mobile

# Start dev server
pnpm dev
```

**Expected Output:**
```
Expo dev server started at http://localhost:8081
Scan QR code to open in Expo Go
```

### 3. Verify Desktop Consumer

```bash
python /home/ubuntu/PhoenixDrive_Desktop_Consumer.py --help
```

**Expected Output:**
```
Bobby's PhoenixDrive Desktop Consumer
Usage: python PhoenixDrive_Desktop_Consumer.py [recipe] [options]
```

---

## Test Scenario 1: Hardware Detection

### Objective
Verify that the mobile app can detect real hardware via the backend API.

### Steps

1. **Open mobile app** in Expo Go
2. **Tap Device Wizard** tab
3. **Wait for hardware detection** (should show loading indicator)

### Expected Results

✅ **CPU Information:**
- Correct processor name (e.g., "Intel Core i7-12700H")
- Correct architecture (x86_64, arm64, etc.)
- Correct core/thread count

✅ **Memory:**
- Total RAM displayed correctly
- Module information shown

✅ **Storage:**
- Correct total storage size
- Available space shown

✅ **Compatibility:**
- Compatible OSes listed (Windows, Linux, ChromeOS, etc.)
- Incompatible OSes marked with reason
- Example: "Apple Silicon arm64 - x86-64 ISOs not compatible"

### Troubleshooting

**Issue:** Hardware detection times out
```bash
# Check API logs
tail -f /home/ubuntu/phoenix-core-mobile/server/api.log

# Test API directly
curl -X POST http://localhost:5000/api/v1/hardware/detect \
  -H "Content-Type: application/json" \
  -d '{"include_storage": true}'
```

**Issue:** Incorrect CPU information
```bash
# Verify hardware detection on backend
python -c "from src.core.hardware_detector import HardwareDetector; print(HardwareDetector().detect())"
```

---

## Test Scenario 2: USB Device Enumeration

### Objective
Verify that the mobile app can detect real USB devices.

### Steps

1. **Connect USB drive** (at least 4GB)
2. **Open USB Builder** tab
3. **Tap "Select USB Device"** (should show loading)
4. **Wait for USB enumeration**

### Expected Results

✅ **USB Device Listed:**
- Correct vendor/model name
- Correct size in GB
- Correct filesystem (exFAT, FAT32, NTFS, etc.)
- Device path shown (e.g., /dev/sdb)
- Health status displayed

✅ **Device Health:**
- "healthy" status for good drives
- Warning if drive has issues

✅ **Write Speed:**
- Estimated write speed shown (MB/s)

### Troubleshooting

**Issue:** USB device not detected
```bash
# List USB devices on system
lsblk

# Test API directly
curl http://localhost:5000/api/v1/usb/devices?min_size_gb=4

# Check permissions
ls -la /dev/sd*
```

**Issue:** Wrong device detected
```bash
# Verify USB device path
sudo fdisk -l

# Test with specific device
curl -X POST http://localhost:5000/api/v1/usb/devices \
  -H "Content-Type: application/json" \
  -d '{"device_path": "/dev/sdb"}'
```

---

## Test Scenario 3: Recipe Building

### Objective
Verify that the mobile app can build a recipe with real hardware and device data.

### Steps

1. **Select USB Device** (from previous test)
2. **Select Operating Systems:**
   - Windows 11
   - Ubuntu 22.04 LTS
3. **Add Tools:**
   - GParted
   - Clonezilla
4. **Review Recipe:**
   - Total size should be ~10 GB
   - Should fit on USB device
5. **Tap "Build USB"** (initiates recipe building)

### Expected Results

✅ **Recipe Created:**
- Recipe ID generated
- Name set correctly
- Deployment type: MULTIBOOT
- All selected OSes included
- All selected tools included

✅ **Size Calculation:**
- Windows 11: ~5.5 GB
- Ubuntu 22.04: ~3.2 GB
- GParted: ~0.8 GB
- Clonezilla: ~1.2 GB
- **Total: ~10.7 GB**

✅ **Validation:**
- Recipe fits on USB device
- No conflicts between OSes
- Bootloader configured (GRUB)

### Troubleshooting

**Issue:** Recipe building fails
```bash
# Check API logs
tail -f /home/ubuntu/phoenix-core-mobile/server/api.log

# Test recipe building directly
curl -X POST http://localhost:5000/api/v1/recipe/build \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Recipe",
    "deployment_type": "MULTIBOOT",
    "os_selections": ["windows_11", "ubuntu_22_04"],
    "tool_selections": ["gparted"],
    "target_device_id": "usb-device-id",
    "target_device_size_gb": 64
  }'
```

**Issue:** Recipe too large for USB
- Reduce number of OSes
- Remove optional tools
- Use smaller OS versions

---

## Test Scenario 4: Real-Time Progress Streaming

### Objective
Verify that build progress updates stream in real-time to the mobile UI.

### Steps

1. **Complete Recipe Building** (from previous test)
2. **Tap "Build USB"** to start actual build
3. **Watch progress indicator** on mobile app
4. **Monitor real-time updates:**
   - Overall progress percentage
   - Current stage (downloading, partitioning, writing, verifying)
   - Write speed (MB/s)
   - Estimated time remaining (minutes)

### Expected Results

✅ **Progress Updates:**
- Updates every 1-2 seconds
- Progress bar moves smoothly
- Percentage increases continuously

✅ **Stage Information:**
- Shows current operation (e.g., "Writing image: 45%")
- Transitions between stages (download → partition → write → verify)

✅ **Performance Metrics:**
- Write speed displayed (50-100 MB/s typical)
- ETA updates as build progresses
- Accurate time remaining

### Troubleshooting

**Issue:** Progress not updating
```bash
# Check WebSocket connection
# In browser console:
console.log('WebSocket connected:', socket.connected);

# Check API logs for WebSocket events
tail -f /home/ubuntu/phoenix-core-mobile/server/api.log | grep -i websocket

# Test polling fallback
curl http://localhost:5000/api/v1/usb/build/build-id/status
```

**Issue:** Progress stuck at certain percentage
```bash
# Check if build process is actually running
ps aux | grep python

# Check USB device status
lsblk

# Check disk I/O
iostat -x 1 5
```

---

## Test Scenario 5: Recipe Caching

### Objective
Verify that recipes are saved locally and can be reused.

### Steps

1. **Complete a recipe build** (from previous test)
2. **Close mobile app** (kill Expo Go)
3. **Reopen mobile app**
4. **Go to USB Builder**
5. **Tap "Review"** step
6. **Look for "Saved Recipes"** section

### Expected Results

✅ **Recipe Persisted:**
- Previous recipe appears in "Saved Recipes"
- Recipe name correct
- OS and tool selections preserved
- Use count incremented

✅ **Recipe Reuse:**
- Can tap saved recipe to load it
- All settings restored
- Can build same USB again without re-selecting

✅ **AsyncStorage:**
- Recipe stored in device storage
- Survives app restart
- Multiple recipes can be saved

### Troubleshooting

**Issue:** Recipes not persisting
```bash
# Check AsyncStorage on device
# In Expo Go console:
import AsyncStorage from '@react-native-async-storage/async-storage';
AsyncStorage.getItem('@phoenixdrive_recipes').then(console.log);

# Clear AsyncStorage if corrupted
AsyncStorage.removeItem('@phoenixdrive_recipes');
```

**Issue:** Recipe data corrupted
```bash
# Verify recipe JSON format
curl http://localhost:5000/api/v1/recipe/build | jq .

# Re-save recipe
# In mobile app: delete recipe and rebuild
```

---

## Test Scenario 6: Desktop Consumer Integration

### Objective
Verify that the desktop consumer can read recipes and build USBs.

### Steps

1. **Export recipe from mobile app:**
   - Tap "Export" after building recipe
   - Choose "JSON" format
   - Download or copy to clipboard

2. **Save recipe to desktop:**
   ```bash
   # Save recipe.json to current directory
   cat > recipe.json << 'EOF'
   {
     "recipe_id": "recipe-12345",
     "name": "Test Recipe",
     "deployment_type": "MULTIBOOT",
     ...
   }
   EOF
   ```

3. **List USB devices:**
   ```bash
   python /home/ubuntu/PhoenixDrive_Desktop_Consumer.py --list-devices
   ```

4. **Show recipe summary:**
   ```bash
   python /home/ubuntu/PhoenixDrive_Desktop_Consumer.py recipe.json --summary
   ```

5. **Dry-run build (no actual write):**
   ```bash
   python /home/ubuntu/PhoenixDrive_Desktop_Consumer.py recipe.json \
     --device /dev/sdb \
     --dry-run
   ```

6. **Actual build (with confirmation):**
   ```bash
   sudo python /home/ubuntu/PhoenixDrive_Desktop_Consumer.py recipe.json \
     --device /dev/sdb
   ```

### Expected Results

✅ **Device Listing:**
- All USB devices shown with size and path
- Correct device identification

✅ **Recipe Summary:**
- Recipe name and type
- OSes and tools listed
- Total size calculated
- Estimated write time

✅ **Dry-Run:**
- No actual data written
- Validation passes
- Shows what would happen

✅ **Actual Build:**
- Prompts for confirmation
- Requires sudo for USB write
- Shows progress
- Verifies write integrity
- Reports success or failure

### Troubleshooting

**Issue:** Device not found
```bash
# List all block devices
lsblk

# Check device permissions
ls -la /dev/sd*

# Run with sudo
sudo python PhoenixDrive_Desktop_Consumer.py recipe.json --list-devices
```

**Issue:** Build fails with permission error
```bash
# Run with sudo
sudo python /home/ubuntu/PhoenixDrive_Desktop_Consumer.py recipe.json --device /dev/sdb

# Check USB device status
sudo fdisk -l /dev/sdb
```

**Issue:** Recipe validation fails
```bash
# Validate recipe JSON format
python -c "import json; json.load(open('recipe.json'))"

# Check recipe compatibility
python /home/ubuntu/PhoenixDrive_Desktop_Consumer.py recipe.json --validate
```

---

## Test Scenario 7: QR Code Export/Import

### Objective
Verify that recipes can be exported as QR codes and scanned on desktop.

### Steps

1. **Export recipe as QR code:**
   - Complete recipe build
   - Tap "Export"
   - Choose "QR Code"
   - Screenshot or save QR code

2. **Scan QR code on desktop:**
   ```bash
   python /home/ubuntu/PhoenixDrive_Desktop_Consumer.py --scan-qr
   ```

3. **Build from scanned recipe:**
   ```bash
   python /home/ubuntu/PhoenixDrive_Desktop_Consumer.py --device /dev/sdb
   ```

### Expected Results

✅ **QR Code Generated:**
- QR code displays on mobile
- Can be screenshotted
- Contains compressed recipe JSON

✅ **QR Code Scanning:**
- Desktop app can scan QR code
- Recipe extracted correctly
- All settings preserved

✅ **Build from QR:**
- Same as JSON-based build
- All OSes and tools included
- Correct size calculation

### Troubleshooting

**Issue:** QR code too large
- Reduce recipe complexity
- Use JSON export instead
- Compress recipe data

**Issue:** QR code scanning fails
```bash
# Test QR code format
python -c "import qrcode; qr = qrcode.QRCode(); qr.add_data('test'); qr.make()"

# Verify camera/scanner
# Use external QR scanner app to verify QR code
```

---

## Full End-to-End Test Script

```bash
#!/bin/bash
# Complete end-to-end test

echo "=== Bobby's PhoenixDrive E2E Test ==="
echo ""

# 1. Start backend API
echo "1. Starting backend API..."
cd /home/ubuntu/phoenix-core-mobile/server
python api.py &
API_PID=$!
sleep 2

# 2. Health check
echo "2. Checking API health..."
curl -s http://localhost:5000/api/v1/health | jq .

# 3. Test hardware detection
echo "3. Testing hardware detection..."
curl -s -X POST http://localhost:5000/api/v1/hardware/detect \
  -H "Content-Type: application/json" \
  -d '{"include_storage": true}' | jq '.hardware.cpu'

# 4. Test USB enumeration
echo "4. Testing USB enumeration..."
curl -s http://localhost:5000/api/v1/usb/devices?min_size_gb=4 | jq '.devices[0]'

# 5. Test recipe building
echo "5. Testing recipe building..."
curl -s -X POST http://localhost:5000/api/v1/recipe/build \
  -H "Content-Type: application/json" \
  -d '{
    "name": "E2E Test Recipe",
    "deployment_type": "MULTIBOOT",
    "os_selections": ["windows_11", "ubuntu_22_04"],
    "tool_selections": ["gparted"],
    "target_device_id": "test-device",
    "target_device_size_gb": 64
  }' | jq '.recipe.recipe_id'

# 6. Cleanup
echo "6. Cleaning up..."
kill $API_PID

echo ""
echo "=== E2E Test Complete ==="
```

---

## Performance Benchmarks

| Operation | Expected Time | Tolerance |
|-----------|---------------|-----------|
| Hardware detection | 2-5 seconds | ±1 second |
| USB enumeration | 1-3 seconds | ±1 second |
| Recipe building | 5-10 seconds | ±2 seconds |
| USB write (10GB) | 10-15 minutes | ±2 minutes |
| Progress update interval | 1-2 seconds | ±0.5 seconds |

---

## Checklist

- [ ] Backend API starts without errors
- [ ] Hardware detection returns correct data
- [ ] USB devices enumerated correctly
- [ ] Recipe building succeeds
- [ ] Real-time progress updates work
- [ ] Recipes persist in AsyncStorage
- [ ] Desktop consumer reads recipes
- [ ] QR code export/import works
- [ ] USB build completes successfully
- [ ] All error messages are clear

---

## Support

For issues:
1. Check logs: `tail -f /home/ubuntu/phoenix-core-mobile/server/api.log`
2. Review API docs: `/home/ubuntu/BACKEND_SCHEMA.md`
3. Check PhoenixCore: `/home/ubuntu/PhoenixCore-/README.md`
4. Submit issue on GitHub
