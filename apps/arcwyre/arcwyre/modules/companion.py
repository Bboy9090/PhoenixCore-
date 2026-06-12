import os
import qrcode
from PIL import ImageQt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFileDialog, QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QImage

from arcwyre.theme import COLORS

class CompanionModule(QWidget):
    """Module to distribute the Mobile Companion App."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Header
        title = QLabel("📱 Arcwyre Mobile Companion")
        title.setStyleSheet(f"color: {COLORS['primary']}; font-size: 28px; font-weight: 800; letter-spacing: -1px;")
        layout.addWidget(title)
        
        desc = QLabel(
            "Build your USB recipes directly from your phone. Scan the QR code to "
            "install the companion app, or export the Android APK directly to your "
            "Phoenix Key to sideload it offline."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 15px; line-height: 1.5;")
        layout.addWidget(desc)
        
        # Split into two sections: QR Code and APK Export
        grid = QHBoxLayout()
        grid.setSpacing(30)
        
        # QR Code Group
        qr_group = QGroupBox("Scan to Install (OTA)")
        qr_layout = QVBoxLayout(qr_group)
        qr_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.qr_label = QLabel()
        self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._generate_qr()
        qr_layout.addWidget(self.qr_label)
        
        qr_help = QLabel("Point your iOS/Android camera at the code above.")
        qr_help.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px; text-align: center;")
        qr_help.setAlignment(Qt.AlignmentFlag.AlignCenter)
        qr_layout.addWidget(qr_help)
        
        grid.addWidget(qr_group)
        
        # APK Export Group
        apk_group = QGroupBox("Export Android APK (Offline)")
        apk_layout = QVBoxLayout(apk_group)
        apk_layout.setSpacing(15)
        
        apk_info = QLabel("Sideload the companion app directly onto an Android device or your Phoenix Key without an internet connection.")
        apk_info.setWordWrap(True)
        apk_info.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        apk_layout.addWidget(apk_info)
        
        export_btn = QPushButton("📦 Export ArcwyreCompanion.apk")
        export_btn.setStyleSheet(f"background-color: {COLORS['primary']}; color: #000; font-weight: bold; padding: 12px; border-radius: 8px;")
        export_btn.clicked.connect(self._export_apk)
        apk_layout.addWidget(export_btn)
        apk_layout.addStretch()
        
        grid.addWidget(apk_group)
        
        layout.addLayout(grid)
        layout.addStretch()
        
    def _generate_qr(self):
        """Generate a QR code dynamically."""
        try:
            # We would point this to the Expo App Store link or local dev server
            data = "exp://localhost:8081" 
            qr = qrcode.QRCode(version=1, box_size=10, border=2)
            qr.add_data(data)
            qr.make(fit=True)
            
            # Generate image with colors matching the theme
            # Primary cyan for the code, transparent/dark for the background
            img = qr.make_image(fill_color="#00D0E5", back_color="#2C2C2E")
            
            # Convert PIL image to QPixmap
            qim = ImageQt.ImageQt(img)
            pix = QPixmap.fromImage(qim)
            
            self.qr_label.setPixmap(pix.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio))
        except Exception as e:
            self.qr_label.setText(f"QR Generation Failed: {e}")
            
    def _export_apk(self):
        """Simulate exporting the APK."""
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Mobile Companion APK", "ArcwyreCompanion.apk", "APK Files (*.apk)"
        )
        
        if path:
            try:
                # In production, this would copy a bundled APK from assets
                with open(path, 'w') as f:
                    f.write("DUMMY APK DATA - BUNDLE ACTUAL APK IN PYINSTALLER BUILD")
                    
                QMessageBox.information(
                    self, "Export Complete", 
                    f"Successfully exported ArcwyreCompanion.apk to:\n{path}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export APK: {str(e)}")
