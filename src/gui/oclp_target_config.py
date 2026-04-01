"""
BootForge OCLP Target & Kext Configuration
Choose target Mac model, kexts, and OpenCore settings.
"""

import logging
from typing import Dict, List, Optional, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QComboBox, QCheckBox, QScrollArea, QFrame, QFormLayout,
    QLineEdit, QPushButton, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from src.core.hardware_profiles import (
    get_mac_model_data,
    get_mac_oclp_requirements,
    get_patch_requirements_for_model,
    is_mac_oclp_compatible,
)
from src.core.hardware_detector import DetectedHardware


logger = logging.getLogger(__name__)

MACOS_VERSIONS = ["11.0", "12.0", "13.0", "14.0", "15.0"]
SIP_OPTIONS = ["disabled", "partial", "enabled"]


class OCLPTargetKextConfigWidget(QWidget):
    """
    Target host, kext selection, and OpenCore settings.
    Used when building for unsupported Macs.
    """
    config_changed = pyqtSignal(dict)

    def __init__(self, detected_hardware: Optional[DetectedHardware] = None, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.detected_hardware = detected_hardware
        self._kext_checkboxes: Dict[str, Dict[str, QCheckBox]] = {}
        self._kext_category_grids: Dict[str, QGridLayout] = {}
        self._kext_category_frames: Dict[str, QWidget] = {}
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout()

        # Target host section
        target_group = QGroupBox("Target Host Computer")
        target_layout = QFormLayout()

        self.model_combo = QComboBox()
        self.model_combo.setMinimumWidth(300)
        self.model_combo.setEditable(True)
        self.model_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self._populate_model_combo()
        target_layout.addRow("Mac Model:", self.model_combo)

        self.macos_combo = QComboBox()
        self.macos_combo.addItems(MACOS_VERSIONS)
        self.macos_combo.setCurrentText("13.0")
        target_layout.addRow("Target macOS:", self.macos_combo)

        target_group.setLayout(target_layout)
        layout.addWidget(target_group)

        # Kext selection section
        kext_group = QGroupBox("Kexts & Patches")
        kext_layout = QVBoxLayout()

        self._add_kext_category(kext_layout, "Graphics", "graphics_patches")
        self._add_kext_category(kext_layout, "Audio", "audio_patches")
        self._add_kext_category(kext_layout, "WiFi / Bluetooth", "wifi_bluetooth_patches")
        self._add_kext_category(kext_layout, "USB", "usb_patches")

        kext_group.setLayout(kext_layout)
        layout.addWidget(kext_group)

        # Settings section
        settings_group = QGroupBox("OpenCore Settings")
        settings_layout = QFormLayout()

        self.sip_combo = QComboBox()
        self.sip_combo.addItems(SIP_OPTIONS)
        self.sip_combo.setCurrentText("disabled")
        settings_layout.addRow("SIP:", self.sip_combo)

        self.secure_boot_label = QLabel("(from model)")
        self.secure_boot_label.setStyleSheet("color: gray;")
        settings_layout.addRow("SecureBootModel:", self.secure_boot_label)

        self.verbose_check = QCheckBox("Verbose boot")
        self.verbose_check.setChecked(False)
        settings_layout.addRow("", self.verbose_check)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        # Buttons
        btn_layout = QHBoxLayout()
        self.apply_btn = QPushButton("Apply Configuration")
        self.apply_btn.clicked.connect(self._emit_config)
        btn_layout.addWidget(self.apply_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.setLayout(layout)

        self.model_combo.currentIndexChanged.connect(self._on_model_changed)
        self.macos_combo.currentTextChanged.connect(self._on_model_changed)

        if self.model_combo.currentIndex() >= 0:
            self._on_model_changed()

    def _populate_model_combo(self):
        mac_models = get_mac_model_data()
        oclp_models = [
            (mid, data) for mid, data in mac_models.items()
            if data.get("oclp_compatibility") in ("fully_supported", "partially_supported", "experimental")
        ]
        oclp_models.sort(key=lambda x: (x[1].get("year", 0), x[1]["name"]))

        self.model_combo.clear()
        for model_id, data in oclp_models:
            self.model_combo.addItem(f"{data['name']} ({model_id})", model_id)

        if self.detected_hardware and self.detected_hardware.system_model:
            model_id = self.detected_hardware.system_model
            for i in range(self.model_combo.count()):
                if self.model_combo.itemData(i) == model_id:
                    self.model_combo.setCurrentIndex(i)
                    break

    def _add_kext_category(self, parent_layout: QVBoxLayout, label: str, key: str):
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        flay = QVBoxLayout()
        flay.addWidget(QLabel(f"<b>{label}</b>"))
        self._kext_checkboxes[key] = {}
        place_label = QLabel("(Select model to load)")
        place_label.setObjectName(f"{key}_placeholder")
        flay.addWidget(place_label)

        grid = QGridLayout()
        flay.addLayout(grid)
        frame.setLayout(flay)
        parent_layout.addWidget(frame)
        self._kext_category_grids[key] = grid
        self._kext_category_frames[key] = (place_label, frame)

    def _on_model_changed(self):
        model_id = self._get_selected_model_id()
        if not model_id:
            return

        mac_models = get_mac_model_data()
        if model_id not in mac_models:
            return

        data = mac_models[model_id]
        sip = data.get("sip_requirements") or "disabled"
        if sip in SIP_OPTIONS:
            self.sip_combo.setCurrentText(sip)
        self.secure_boot_label.setText(data.get("secure_boot_model") or "(auto)")
        self.secure_boot_label.setStyleSheet("")

        for key in ["graphics_patches", "audio_patches", "wifi_bluetooth_patches", "usb_patches"]:
            self._clear_kext_grid(key)
            patches = data.get(key, [])
            grid = self._kext_category_grids.get(key)
            if not grid:
                continue
            placeholder = self._kext_category_frames.get(key, (None, None))[0]
            if placeholder:
                placeholder.setVisible(False)
            for i, kext in enumerate(patches):
                cb = QCheckBox(kext)
                cb.setChecked(True)
                row, col = i // 3, i % 3
                grid.addWidget(cb, row, col)
                self._kext_checkboxes[key][kext] = cb

    def _clear_kext_grid(self, key: str):
        grid = self._kext_category_grids.get(key)
        placeholder_tuple = self._kext_category_frames.get(key)
        if grid:
            while grid.count():
                item = grid.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
        self._kext_checkboxes[key] = {}
        if placeholder_tuple:
            placeholder_tuple[0].setVisible(True)

    def _get_selected_model_id(self) -> Optional[str]:
        idx = self.model_combo.currentIndex()
        if idx >= 0:
            vid = self.model_combo.itemData(idx)
            if vid:
                return vid
        text = self.model_combo.currentText()
        if "(" in text and ")" in text:
            return text.split("(")[-1].rstrip(")")
        return text.strip() or None

    def get_config(self) -> Dict[str, Any]:
        model_id = self._get_selected_model_id()
        mac_models = get_mac_model_data()
        data = mac_models.get(model_id, {}) if model_id else {}

        kexts = {}
        for key in ["graphics_patches", "audio_patches", "wifi_bluetooth_patches", "usb_patches"]:
            kexts[key] = [
                k for k, cb in self._kext_checkboxes.get(key, {}).items()
                if cb.isChecked()
            ]

        return {
            "model_id": model_id,
            "model_name": data.get("name", "Unknown"),
            "target_macos": self.macos_combo.currentText(),
            "kexts": kexts,
            "sip_requirements": self.sip_combo.currentText(),
            "secure_boot_model": data.get("secure_boot_model"),
            "verbose_boot": self.verbose_check.isChecked(),
        }

    def _emit_config(self):
        self.config_changed.emit(self.get_config())
