"""
Phoenix Core Status Widget
System status monitoring with premium Electric Blue & Gold styling
"""

import logging
from typing import List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QProgressBar, QListWidget, QListWidgetItem,
    QGridLayout, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPalette

from src.core.system_monitor import SystemInfo
from src.core.disk_manager import DiskInfo


# Phoenix Core progress bar chunk colors
_STYLE_CPU_HIGH = "QProgressBar::chunk { background-color: #f43f5e; border-radius: 4px; }"
_STYLE_CPU_MED  = "QProgressBar::chunk { background-color: #ffd700; border-radius: 4px; }"
_STYLE_CPU_LOW  = "QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00d2ff, stop:1 #0088cc); border-radius: 4px; }"

# Phoenix Core group box style (electric blue title, dark card background)
_GROUP_STYLE = """
    QGroupBox {{
        color: #ffd700;
        font-weight: 700;
        font-size: 11px;
        letter-spacing: 1px;
        border: 1px solid rgba(0, 210, 255, 0.2);
        border-radius: 8px;
        margin-top: 12px;
        padding-top: 10px;
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #080c16, stop:1 #050811);
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 2px 10px;
        color: #ffd700;
        background: rgba(255, 215, 0, 0.08);
        border: 1px solid rgba(255, 215, 0, 0.3);
        border-radius: 4px;
    }}
    QLabel {{ color: #94a3b8; background: transparent; }}
"""


class SystemStatusWidget(QWidget):
    """System status display widget"""
    
    def __init__(self):
        super().__init__()
        self._last_cpu_style: Optional[str] = None
        self._last_mem_style: Optional[str] = None
        self._last_temp_style: Optional[str] = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup status UI"""
        layout = QVBoxLayout(self)
        
        # CPU Status — electric blue value label
        cpu_group = QGroupBox("CPU")
        cpu_group.setStyleSheet(_GROUP_STYLE)
        cpu_layout = QGridLayout(cpu_group)
        
        self.cpu_label = QLabel("--")
        self.cpu_label.setStyleSheet("color: #00d2ff; font-weight: 700; font-size: 13px;")
        self.cpu_progress = QProgressBar()
        self.cpu_progress.setMaximum(100)
        self.cpu_progress.setStyleSheet(_STYLE_CPU_LOW)
        
        cpu_layout.addWidget(QLabel("Usage:"), 0, 0)
        cpu_layout.addWidget(self.cpu_label, 0, 1)
        cpu_layout.addWidget(self.cpu_progress, 1, 0, 1, 2)
        
        layout.addWidget(cpu_group)
        
        # Memory Status — electric blue value label
        memory_group = QGroupBox("Memory")
        memory_group.setStyleSheet(_GROUP_STYLE)
        memory_layout = QGridLayout(memory_group)
        
        self.memory_label = QLabel("--")
        self.memory_label.setStyleSheet("color: #00d2ff; font-weight: 700; font-size: 13px;")
        self.memory_progress = QProgressBar()
        self.memory_progress.setMaximum(100)
        self.memory_progress.setStyleSheet(_STYLE_CPU_LOW)
        
        memory_layout.addWidget(QLabel("Usage:"), 0, 0)
        memory_layout.addWidget(self.memory_label, 0, 1)
        memory_layout.addWidget(self.memory_progress, 1, 0, 1, 2)
        
        layout.addWidget(memory_group)
        
        # Temperature Status — electric blue value label
        temp_group = QGroupBox("Temperature")
        temp_group.setStyleSheet(_GROUP_STYLE)
        temp_layout = QGridLayout(temp_group)
        
        self.temp_label = QLabel("--")
        self.temp_label.setStyleSheet("color: #00d2ff; font-weight: 700; font-size: 13px;")
        self.temp_progress = QProgressBar()
        self.temp_progress.setMaximum(100)
        self.temp_progress.setStyleSheet(_STYLE_CPU_LOW)
        
        temp_layout.addWidget(QLabel("CPU:"), 0, 0)
        temp_layout.addWidget(self.temp_label, 0, 1)
        temp_layout.addWidget(self.temp_progress, 1, 0, 1, 2)
        
        layout.addWidget(temp_group)
        
        # Disk I/O Status — gold label values
        io_group = QGroupBox("Disk I/O")
        io_group.setStyleSheet(_GROUP_STYLE)
        io_layout = QGridLayout(io_group)
        
        self.read_label = QLabel("Read: --")
        self.read_label.setStyleSheet("color: #00d2ff; font-weight: 600;")
        self.write_label = QLabel("Write: --")
        self.write_label.setStyleSheet("color: #00d2ff; font-weight: 600;")
        
        io_layout.addWidget(self.read_label, 0, 0)
        io_layout.addWidget(self.write_label, 0, 1)
        
        layout.addWidget(io_group)
        
        layout.addStretch()
    
    def update_system_info(self, info: SystemInfo):
        """Update system information display"""
        # CPU
        self.cpu_label.setText(f"{info.cpu_percent:.1f}%")
        self.cpu_progress.setValue(int(info.cpu_percent))
        
        cpu_style = _STYLE_CPU_HIGH if info.cpu_percent > 80 else (_STYLE_CPU_MED if info.cpu_percent > 60 else _STYLE_CPU_LOW)
        if cpu_style != self._last_cpu_style:
            self.cpu_progress.setStyleSheet(cpu_style)
            self._last_cpu_style = cpu_style
        
        # Memory
        self.memory_label.setText(f"{info.memory_percent:.1f}%")
        self.memory_progress.setValue(int(info.memory_percent))
        
        mem_style = _STYLE_CPU_HIGH if info.memory_percent > 90 else (_STYLE_CPU_MED if info.memory_percent > 75 else _STYLE_CPU_LOW)
        if mem_style != self._last_mem_style:
            self.memory_progress.setStyleSheet(mem_style)
            self._last_mem_style = mem_style
        
        # Temperature
        if info.temperature is not None:
            self.temp_label.setText(f"{info.temperature:.1f}°C")
            temp_percent = min(100, (info.temperature / 100) * 100)  # Scale to 100%
            self.temp_progress.setValue(int(temp_percent))
            
            temp_style = _STYLE_CPU_HIGH if info.temperature > 85 else (_STYLE_CPU_MED if info.temperature > 70 else _STYLE_CPU_LOW)
            if temp_style != self._last_temp_style:
                self.temp_progress.setStyleSheet(temp_style)
                self._last_temp_style = temp_style
        else:
            self.temp_label.setText("--")
            self.temp_progress.setValue(0)
            if self._last_temp_style != _STYLE_CPU_LOW:
                self.temp_progress.setStyleSheet(_STYLE_CPU_LOW)
                self._last_temp_style = _STYLE_CPU_LOW
        
        # Disk I/O (null-safe)
        disk_io = getattr(info, "disk_io", None) or {}
        read_mbps = disk_io.get("read", 0) / (1024 * 1024)
        write_mbps = disk_io.get("write", 0) / (1024 * 1024)
        
        self.read_label.setText(f"Read: {read_mbps:.1f} MB/s")
        self.write_label.setText(f"Write: {write_mbps:.1f} MB/s")


class DeviceListWidget(QWidget):
    """USB device list widget"""
    
    def __init__(self):
        super().__init__()
        self.devices = []
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup device list UI"""
        layout = QVBoxLayout(self)
        
        # Device list
        device_group = QGroupBox("⚡ USB Devices")
        device_group.setStyleSheet(_GROUP_STYLE)
        device_layout = QVBoxLayout(device_group)
        
        self.device_list = QListWidget()
        device_layout.addWidget(self.device_list)
        
        layout.addWidget(device_group)
    
    def update_device_list(self, devices: List[DiskInfo]):
        """Update device list"""
        self.devices = devices
        self.device_list.clear()
        
        if not devices:
            item = QListWidgetItem("No USB devices detected")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.device_list.addItem(item)
            return
        
        for device in devices:
            size_gb = device.size_bytes / (1024**3)
            text = f"{device.name}\n"
            text += f"Size: {size_gb:.1f} GB\n"
            text += f"Path: {device.path}\n"
            text += f"Health: {device.health_status}"
            
            item = QListWidgetItem(text)
            
            # Set item color based on health
            if device.health_status == "Good":
                item.setBackground(QPalette().color(QPalette.ColorRole.Base))
            else:
                item.setBackground(QPalette().color(QPalette.ColorRole.AlternateBase))
            
            self.device_list.addItem(item)


class StatusWidget(QWidget):
    """Main status widget combining system and device status"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup main status UI with Phoenix Core card container"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        # Phoenix Core branded section header
        header_label = QLabel("⚡ REAL-TIME HEALTH")
        header_font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        header_label.setFont(header_font)
        header_label.setStyleSheet("""
            QLabel {
                color: #ffd700;
                letter-spacing: 2px;
                padding: 6px 10px 4px 14px;
                border-left: 3px solid #00d2ff;
                background: transparent;
            }
        """)
        layout.addWidget(header_label)
        
        # System status
        self.system_status = SystemStatusWidget()
        layout.addWidget(self.system_status)
        
        # Device list
        self.device_list = DeviceListWidget()
        layout.addWidget(self.device_list)
    
    def update_system_info(self, info: SystemInfo):
        """Update system information"""
        self.system_status.update_system_info(info)
    
    def update_device_list(self, devices: List[DiskInfo]):
        """Update device list"""
        self.device_list.update_device_list(devices)