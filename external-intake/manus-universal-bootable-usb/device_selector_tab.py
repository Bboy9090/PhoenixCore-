"""
Device Selector Tab - Detect and select USB devices
"""

import logging
from typing import Dict, List, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
    QListWidgetItem, QLabel, QMessageBox, QGroupBox, QCheckBox,
    QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import pyqtSignal, Qt, QThread, QTimer
from PyQt6.QtGui import QFont, QColor, QIcon

logger = logging.getLogger(__name__)


class DeviceDetectionThread(QThread):
    """Background thread for USB device detection"""
    
    devices_detected = pyqtSignal(list)  # List of device dicts
    error_occurred = pyqtSignal(str)  # Error message
    
    def run(self):
        """Detect USB devices"""
        try:
            import psutil
            
            devices = []
            
            # Get all disk partitions
            partitions = psutil.disk_partitions()
            
            for partition in partitions:
                # Filter for removable devices
                if partition.fstype and 'removable' in partition.opts.lower() or 'usb' in partition.device.lower():
                    try:
                        usage = psutil.disk_usage(partition.mountpoint)
                        device = {
                            'path': partition.device,
                            'name': partition.device.split('/')[-1],
                            'mountpoint': partition.mountpoint,
                            'fstype': partition.fstype,
                            'total_gb': usage.total / (1024**3),
                            'used_gb': usage.used / (1024**3),
                            'free_gb': usage.free / (1024**3),
                            'percent_used': usage.percent
                        }
                        devices.append(device)
                    except Exception as e:
                        logger.warning(f"Could not get usage for {partition.device}: {e}")
                        continue
            
            self.devices_detected.emit(devices)
        
        except Exception as e:
            self.error_occurred.emit(f"Device detection error: {str(e)}")


class DeviceSelectorTab(QWidget):
    """Tab for selecting target USB device"""
    
    device_selected = pyqtSignal(str)  # Device path
    
    def __init__(self):
        super().__init__()
        self.detected_devices = []
        self.selected_device = None
        self.detection_thread = None
        self.init_ui()
        self.refresh_devices()
    
    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Select USB Device")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Warning
        warning = QLabel(
            "⚠️ WARNING: All data on the selected device will be erased!\n"
            "Make sure you select the correct USB device."
        )
        warning.setStyleSheet("color: red; font-weight: bold;")
        warning.setWordWrap(True)
        layout.addWidget(warning)
        
        # Device list
        device_group = QGroupBox("Available USB Devices")
        device_layout = QVBoxLayout()
        
        # Table for device display
        self.device_table = QTableWidget()
        self.device_table.setColumnCount(5)
        self.device_table.setHorizontalHeaderLabels([
            "Device", "Size (GB)", "Used (GB)", "Free (GB)", "Filesystem"
        ])
        self.device_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.device_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.device_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.device_table.itemSelectionChanged.connect(self.on_device_selected)
        
        device_layout.addWidget(self.device_table)
        
        device_group.setLayout(device_layout)
        layout.addWidget(device_group)
        
        # Device details
        details_group = QGroupBox("Device Details")
        details_layout = QVBoxLayout()
        
        self.details_text = QLabel("Select a device to view details")
        self.details_text.setWordWrap(True)
        details_layout.addWidget(self.details_text)
        
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)
        
        # Safety options
        safety_group = QGroupBox("Safety Options")
        safety_layout = QVBoxLayout()
        
        self.verify_checkbox = QCheckBox("Verify written data after build")
        self.verify_checkbox.setChecked(True)
        safety_layout.addWidget(self.verify_checkbox)
        
        self.eject_checkbox = QCheckBox("Eject device after build")
        self.eject_checkbox.setChecked(True)
        safety_layout.addWidget(self.eject_checkbox)
        
        safety_group.setLayout(safety_layout)
        layout.addWidget(safety_group)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("Refresh Devices")
        self.refresh_btn.clicked.connect(self.refresh_devices)
        button_layout.addWidget(self.refresh_btn)
        
        button_layout.addStretch()
        
        self.select_btn = QPushButton("Select Device")
        self.select_btn.clicked.connect(self.confirm_selection)
        self.select_btn.setEnabled(False)
        button_layout.addWidget(self.select_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def refresh_devices(self):
        """Refresh USB device list"""
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("Scanning...")
        
        self.detection_thread = DeviceDetectionThread()
        self.detection_thread.devices_detected.connect(self.on_devices_detected)
        self.detection_thread.error_occurred.connect(self.on_detection_error)
        self.detection_thread.start()
    
    def on_devices_detected(self, devices: List[Dict]):
        """Handle devices detected"""
        self.detected_devices = devices
        self.device_table.setRowCount(0)
        
        if not devices:
            self.details_text.setText("No USB devices detected. Please connect a USB device.")
            self.refresh_btn.setEnabled(True)
            self.refresh_btn.setText("Refresh Devices")
            return
        
        # Populate table
        for i, device in enumerate(devices):
            self.device_table.insertRow(i)
            
            # Device name
            name_item = QTableWidgetItem(device['name'])
            self.device_table.setItem(i, 0, name_item)
            
            # Total size
            size_item = QTableWidgetItem(f"{device['total_gb']:.1f}")
            self.device_table.setItem(i, 1, size_item)
            
            # Used space
            used_item = QTableWidgetItem(f"{device['used_gb']:.1f}")
            self.device_table.setItem(i, 2, used_item)
            
            # Free space
            free_item = QTableWidgetItem(f"{device['free_gb']:.1f}")
            self.device_table.setItem(i, 3, free_item)
            
            # Filesystem
            fs_item = QTableWidgetItem(device['fstype'])
            self.device_table.setItem(i, 4, fs_item)
        
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("Refresh Devices")
        
        logger.info(f"Detected {len(devices)} USB device(s)")
    
    def on_detection_error(self, error_msg: str):
        """Handle detection error"""
        QMessageBox.critical(self, "Detection Error", error_msg)
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("Refresh Devices")
    
    def on_device_selected(self):
        """Handle device selection in table"""
        selected_rows = self.device_table.selectedIndexes()
        
        if not selected_rows:
            self.select_btn.setEnabled(False)
            self.details_text.setText("No device selected")
            return
        
        row = selected_rows[0].row()
        device = self.detected_devices[row]
        
        # Update details
        details = f"""
        <b>Device:</b> {device['name']}<br>
        <b>Path:</b> {device['path']}<br>
        <b>Total Size:</b> {device['total_gb']:.1f} GB<br>
        <b>Used Space:</b> {device['used_gb']:.1f} GB ({device['percent_used']:.1f}%)<br>
        <b>Free Space:</b> {device['free_gb']:.1f} GB<br>
        <b>Filesystem:</b> {device['fstype']}<br>
        <b>Mountpoint:</b> {device['mountpoint']}<br>
        """
        
        self.details_text.setText(details)
        self.select_btn.setEnabled(True)
        self.selected_device = device
    
    def confirm_selection(self):
        """Confirm device selection"""
        if not self.selected_device:
            QMessageBox.warning(self, "No Device", "Please select a device first")
            return
        
        # Show confirmation
        msg = f"""
        You are about to select:
        
        Device: {self.selected_device['name']}
        Size: {self.selected_device['total_gb']:.1f} GB
        
        WARNING: All data on this device will be erased!
        
        Are you sure?
        """
        
        reply = QMessageBox.warning(
            self, "Confirm Selection", msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.device_selected.emit(self.selected_device['path'])
            logger.info(f"Device selected: {self.selected_device['path']}")
    
    def get_device_info(self, device_path: str) -> Optional[Dict]:
        """Get info for a specific device"""
        for device in self.detected_devices:
            if device['path'] == device_path:
                return device
        return None
