# Bobby's PhoenixDrive — Desktop Recipe Consumer Application

## Overview

The Desktop Recipe Consumer App is a cross-platform desktop application that reads USB deployment recipes created on the mobile app and executes them on the user's computer. It bridges the gap between mobile recipe planning and actual USB creation.

## Architecture

```
┌─────────────────────────────────────────┐
│  Bobby's PhoenixDrive Mobile App        │
│  (React Native + Expo)                  │
│                                         │
│  1. Create Recipe                       │
│  2. Generate QR Code                    │
│  3. Export as JSON                      │
└────────────┬────────────────────────────┘
             │
             ├─ QR Code (scan on desktop)
             └─ JSON File (email/cloud)
             │
┌────────────▼────────────────────────────┐
│  Desktop Recipe Consumer App             │
│  (Electron/PyQt/Qt)                     │
│                                         │
│  1. Scan QR Code or Import JSON         │
│  2. Validate Recipe                     │
│  3. Detect USB Devices                  │
│  4. Execute Build                       │
│  5. Stream Progress to Mobile           │
└────────────┬────────────────────────────┘
             │
             ├─ REST API Calls
             ├─ WebSocket Progress
             └─ Hardware Access
             │
┌────────────▼────────────────────────────┐
│  PhoenixCore Python Modules             │
│  (Hardware Detection, USB Builder)      │
└─────────────────────────────────────────┘
```

## Features

### 1. Recipe Import

**QR Code Scanning**
- Scan QR code generated on mobile app
- Automatically decode recipe JSON
- Validate recipe format and integrity

**File Import**
- Import recipe from JSON file
- Support for email attachments
- Cloud storage integration (Google Drive, Dropbox, OneDrive)

**Manual Entry**
- Paste recipe JSON directly
- Validate and preview before execution

### 2. Device Detection

**USB Device Enumeration**
- Detect all connected USB devices
- Display device info (vendor, model, size, filesystem)
- Show device health status
- Warn about system drives

**Device Validation**
- Verify device is removable storage
- Check for critical system partitions
- Confirm device is safe to write to
- Prevent accidental data loss

### 3. Recipe Execution

**Pre-Build Validation**
- Verify recipe format and integrity
- Check device compatibility
- Validate OS ISO checksums
- Confirm sufficient device space

**Build Process**
- Download OS ISOs (with resume support)
- Create partitions according to recipe
- Write bootloader
- Install OS images
- Verify written data

**Progress Streaming**
- Real-time progress updates to mobile app
- Show current stage (downloading, writing, verifying)
- Display speed, ETA, and percentage complete
- Handle errors and retry logic

### 4. Error Handling

**Graceful Failure**
- Detect and report errors clearly
- Suggest recovery steps
- Allow retry with different settings
- Preserve partial work for recovery

**Safety Checks**
- Multi-layer validation before write
- Confirm before destructive operations
- Prevent data loss scenarios
- Log all operations for audit trail

## Implementation Options

### Option 1: Electron App (Recommended)

**Advantages:**
- Cross-platform (Windows, macOS, Linux)
- Web technologies (HTML, CSS, JavaScript)
- Easy to distribute and update
- Good performance for UI

**Technology Stack:**
- Electron framework
- React for UI
- Node.js backend
- native-usb for device access

**Build Time:** 2-3 weeks

### Option 2: PyQt Desktop App

**Advantages:**
- Direct Python integration with PhoenixCore
- Native look and feel on each platform
- Lightweight and fast
- Easy to package

**Technology Stack:**
- PyQt6 for UI
- Python backend
- Direct PhoenixCore module access
- pyusb for device enumeration

**Build Time:** 1-2 weeks

### Option 3: Qt Application

**Advantages:**
- High performance
- Native UI on all platforms
- Excellent for system-level operations
- Professional appearance

**Technology Stack:**
- Qt 6 framework
- C++ backend
- Direct hardware access
- Qt Quick for modern UI

**Build Time:** 3-4 weeks

## Recommended: PyQt Desktop App

For Bobby's PhoenixDrive, we recommend the PyQt approach because:

1. **Direct PhoenixCore Integration** — No need for API calls, direct Python module access
2. **Faster Development** — Python is faster to develop than C++
3. **Easy Distribution** — PyInstaller creates standalone executables
4. **Cross-Platform** — Works on Windows, macOS, Linux
5. **Lightweight** — Smaller download size than Electron

## PyQt Desktop App Implementation

### File Structure

```
phoenix-drive-desktop/
├── main.py                    # Application entry point
├── requirements.txt           # Python dependencies
├── src/
│   ├── ui/
│   │   ├── main_window.py    # Main application window
│   │   ├── recipe_import.py  # Recipe import dialog
│   │   ├── device_selector.py # USB device selection
│   │   ├── build_progress.py # Build progress display
│   │   └── settings.py       # Application settings
│   ├── core/
│   │   ├── recipe_manager.py # Recipe handling
│   │   ├── device_manager.py # USB device detection
│   │   ├── build_executor.py # Build execution
│   │   └── mobile_sync.py    # Mobile app sync
│   └── utils/
│       ├── qr_scanner.py     # QR code scanning
│       ├── file_handler.py   # File import/export
│       └── logger.py         # Application logging
├── assets/
│   ├── icons/
│   ├── styles/
│   └── resources.qrc
└── build/
    └── build.spec            # PyInstaller spec file
```

### Key Components

#### 1. Main Window (main_window.py)

```python
import sys
from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QTabWidget
from PyQt6.QtCore import Qt

class PhoenixDriveDesktop(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bobby's PhoenixDrive Desktop")
        self.setGeometry(100, 100, 1000, 700)
        
        # Create tabs
        tabs = QTabWidget()
        tabs.addTab(RecipeImportTab(), "Import Recipe")
        tabs.addTab(DeviceSelectorTab(), "Select Device")
        tabs.addTab(BuildProgressTab(), "Build Progress")
        tabs.addTab(SettingsTab(), "Settings")
        
        self.setCentralWidget(tabs)
```

#### 2. Recipe Import (recipe_import.py)

```python
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTextEdit
from PyQt6.QtCore import pyqtSignal
import json
from pyzbar import pyzbar
from PIL import Image

class RecipeImportTab(QWidget):
    recipe_loaded = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # QR code scanner button
        scan_btn = QPushButton("Scan QR Code")
        scan_btn.clicked.connect(self.scan_qr_code)
        layout.addWidget(scan_btn)
        
        # File import button
        import_btn = QPushButton("Import from File")
        import_btn.clicked.connect(self.import_from_file)
        layout.addWidget(import_btn)
        
        # Manual paste area
        self.recipe_text = QTextEdit()
        self.recipe_text.setPlaceholderText("Paste recipe JSON here...")
        layout.addWidget(self.recipe_text)
        
        # Load button
        load_btn = QPushButton("Load Recipe")
        load_btn.clicked.connect(self.load_recipe)
        layout.addWidget(load_btn)
        
        self.setLayout(layout)
    
    def scan_qr_code(self):
        """Scan QR code from webcam"""
        import cv2
        cap = cv2.VideoCapture(0)
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Decode QR codes
            decoded_objects = pyzbar.decode(frame)
            
            for obj in decoded_objects:
                recipe_json = obj.data.decode('utf-8')
                recipe = json.loads(recipe_json)
                self.recipe_loaded.emit(recipe)
                cap.release()
                return
            
            cv2.imshow('QR Code Scanner', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
    
    def import_from_file(self):
        """Import recipe from JSON file"""
        from PyQt6.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getOpenFileName(
            self, "Import Recipe", "", "JSON Files (*.json)"
        )
        if filename:
            with open(filename, 'r') as f:
                recipe = json.load(f)
                self.recipe_loaded.emit(recipe)
                self.recipe_text.setText(json.dumps(recipe, indent=2))
    
    def load_recipe(self):
        """Load recipe from manual paste"""
        try:
            recipe = json.loads(self.recipe_text.toPlainText())
            self.recipe_loaded.emit(recipe)
        except json.JSONDecodeError as e:
            # Show error dialog
            pass
```

#### 3. Device Selector (device_selector.py)

```python
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QPushButton
from PyQt6.QtCore import pyqtSignal
import sys
sys.path.insert(0, '/path/to/PhoenixCore-')

from src.core.disk_manager import DiskManager

class DeviceSelectorTab(QWidget):
    device_selected = pyqtSignal(str)  # device path
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.refresh_devices()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Device list
        self.device_list = QListWidget()
        layout.addWidget(self.device_list)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh Devices")
        refresh_btn.clicked.connect(self.refresh_devices)
        layout.addWidget(refresh_btn)
        
        # Select button
        select_btn = QPushButton("Select Device")
        select_btn.clicked.connect(self.select_device)
        layout.addWidget(select_btn)
        
        self.setLayout(layout)
    
    def refresh_devices(self):
        """Refresh USB device list"""
        self.device_list.clear()
        
        disk_manager = DiskManager()
        devices = disk_manager.get_removable_drives()
        
        for device in devices:
            item_text = f"{device.name} ({device.size_bytes / (1024**3):.1f}GB) - {device.path}"
            item = QListWidgetItem(item_text)
            item.setData(1, device.path)  # Store path in data
            self.device_list.addItem(item)
    
    def select_device(self):
        """Select the highlighted device"""
        current_item = self.device_list.currentItem()
        if current_item:
            device_path = current_item.data(1)
            self.device_selected.emit(device_path)
```

#### 4. Build Executor (build_executor.py)

```python
from PyQt6.QtCore import QThread, pyqtSignal
import sys
sys.path.insert(0, '/path/to/PhoenixCore-')

from src.core.usb_builder import USBBuilder

class BuildExecutorThread(QThread):
    progress_update = pyqtSignal(dict)
    build_complete = pyqtSignal()
    build_error = pyqtSignal(str)
    
    def __init__(self, recipe, device_path):
        super().__init__()
        self.recipe = recipe
        self.device_path = device_path
    
    def run(self):
        try:
            builder = USBBuilder()
            
            def progress_callback(update):
                self.progress_update.emit(update)
            
            builder.build_usb(
                recipe=self.recipe,
                device_path=self.device_path,
                progress_callback=progress_callback
            )
            
            self.build_complete.emit()
        
        except Exception as e:
            self.build_error.emit(str(e))
```

#### 5. Mobile Sync (mobile_sync.py)

```python
import requests
import websocket
import json
from threading import Thread

class MobileSyncManager:
    def __init__(self, api_url="http://localhost:5000"):
        self.api_url = api_url
        self.ws = None
    
    def connect_websocket(self, build_id):
        """Connect to WebSocket for real-time progress"""
        ws_url = f"ws://localhost:5000/ws/build/{build_id}"
        self.ws = websocket.WebSocketApp(
            ws_url,
            on_message=self.on_ws_message,
            on_error=self.on_ws_error,
            on_close=self.on_ws_close
        )
        self.ws.run_forever()
    
    def send_build_progress(self, build_id, progress):
        """Send build progress to mobile app via API"""
        try:
            response = requests.post(
                f"{self.api_url}/api/v1/usb/build/{build_id}/progress",
                json=progress
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Failed to send progress: {e}")
            return False
    
    def on_ws_message(self, ws, message):
        """Handle WebSocket message"""
        data = json.loads(message)
        print(f"Received: {data}")
    
    def on_ws_error(self, ws, error):
        """Handle WebSocket error"""
        print(f"WebSocket error: {error}")
    
    def on_ws_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close"""
        print(f"WebSocket closed: {close_msg}")
```

### Dependencies

```
PyQt6==6.4.2
PyQt6-sip==13.4.1
opencv-python==4.7.0
pyzbar==0.1.9
Pillow==9.5.0
requests==2.31.0
websocket-client==1.5.1
pyusb==1.2.1
```

### Building Standalone Executable

```bash
# Install PyInstaller
pip install pyinstaller

# Build executable
pyinstaller --onefile --windowed \
  --icon=assets/icon.ico \
  --name="PhoenixDrive" \
  main.py

# Output: dist/PhoenixDrive.exe (Windows) or dist/PhoenixDrive (macOS/Linux)
```

## Distribution

### Windows
- Distribute as `.exe` installer using NSIS
- Include PhoenixCore dependencies
- Auto-update support via GitHub releases

### macOS
- Distribute as `.dmg` file
- Code signing for security
- Notarization for Gatekeeper

### Linux
- Distribute as AppImage
- Also provide `.deb` and `.rpm` packages
- Snap package for easy installation

## Integration with Mobile App

### QR Code Export

Mobile app generates QR code containing recipe JSON:

```python
import qrcode
import json

recipe = {...}
recipe_json = json.dumps(recipe)
qr = qrcode.QRCode(version=1, box_size=10, border=5)
qr.add_data(recipe_json)
qr.make(fit=True)
img = qr.make_image(fill_color="black", back_color="white")
img.save("recipe_qr.png")
```

### WebSocket Progress Updates

Desktop app sends progress updates to mobile app:

```json
{
  "type": "progress",
  "buildId": "build-123",
  "stage": "writing",
  "percentage": 45,
  "message": "Writing to USB device...",
  "speed": "120 MB/s",
  "timeRemaining": "10 minutes"
}
```

Mobile app receives and displays updates in real-time.

## Next Steps

1. Choose implementation approach (PyQt recommended)
2. Set up development environment
3. Implement core components
4. Test with real PhoenixCore modules
5. Build and package for distribution
6. Create installation guides
7. Set up auto-update system

## References

- [PyQt6 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- [PyInstaller Documentation](https://pyinstaller.org/)
- [PhoenixCore Repository](https://github.com/Bboy9090/PhoenixCore-)
