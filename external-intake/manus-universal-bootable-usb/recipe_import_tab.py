"""
Recipe Import Tab - Handle recipe import from QR code, file, or manual paste
"""

import json
import logging
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit,
    QLabel, QMessageBox, QFileDialog, QTabWidget, QGroupBox,
    QComboBox, QSpinBox, QCheckBox, QFormLayout
)
from PyQt6.QtCore import pyqtSignal, Qt, QThread, QTimer
from PyQt6.QtGui import QFont, QIcon, QPixmap

logger = logging.getLogger(__name__)


class QRCodeScannerThread(QThread):
    """Background thread for QR code scanning"""
    
    qr_detected = pyqtSignal(str)  # QR code data
    error_occurred = pyqtSignal(str)  # Error message
    
    def __init__(self):
        super().__init__()
        self.is_running = True
    
    def run(self):
        """Run QR code scanner"""
        try:
            import cv2
            from pyzbar import pyzbar
            
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                self.error_occurred.emit("Could not open camera. Please check camera permissions.")
                return
            
            while self.is_running:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Decode QR codes
                decoded_objects = pyzbar.decode(frame)
                
                for obj in decoded_objects:
                    qr_data = obj.data.decode('utf-8')
                    self.qr_detected.emit(qr_data)
                    cap.release()
                    return
                
                # Display frame (optional)
                cv2.imshow('QR Code Scanner', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            cap.release()
            cv2.destroyAllWindows()
        
        except ImportError as e:
            self.error_occurred.emit(f"Required package not installed: {str(e)}\n\nPlease install: pip install opencv-python pyzbar")
        except Exception as e:
            self.error_occurred.emit(f"QR code scanning error: {str(e)}")
    
    def stop(self):
        """Stop scanning"""
        self.is_running = False


class RecipeImportTab(QWidget):
    """Tab for importing recipes from various sources"""
    
    recipe_loaded = pyqtSignal(dict)  # Emitted when recipe is successfully loaded
    
    def __init__(self):
        super().__init__()
        self.scanner_thread = None
        self.current_recipe = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Import Recipe")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Import methods tabs
        import_tabs = QTabWidget()
        
        # Tab 1: QR Code Scanner
        qr_tab = self.create_qr_tab()
        import_tabs.addTab(qr_tab, "📱 Scan QR Code")
        
        # Tab 2: File Import
        file_tab = self.create_file_tab()
        import_tabs.addTab(file_tab, "📁 Import File")
        
        # Tab 3: Manual Paste
        manual_tab = self.create_manual_tab()
        import_tabs.addTab(manual_tab, "📝 Manual Paste")
        
        layout.addWidget(import_tabs)
        
        # Recipe preview
        preview_group = QGroupBox("Recipe Preview")
        preview_layout = QVBoxLayout()
        
        self.recipe_text = QTextEdit()
        self.recipe_text.setReadOnly(True)
        self.recipe_text.setMaximumHeight(150)
        self.recipe_text.setPlaceholderText("Recipe details will appear here...")
        preview_layout.addWidget(self.recipe_text)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_recipe)
        self.clear_btn.setEnabled(False)
        button_layout.addWidget(self.clear_btn)
        
        button_layout.addStretch()
        
        self.validate_btn = QPushButton("Validate Recipe")
        self.validate_btn.clicked.connect(self.validate_recipe)
        self.validate_btn.setEnabled(False)
        button_layout.addWidget(self.validate_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def create_qr_tab(self) -> QWidget:
        """Create QR code scanner tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel(
            "Click 'Start Scanner' to open your camera and scan a QR code containing a recipe.\n\n"
            "Make sure your camera is connected and you have granted camera permissions."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Scanner controls
        controls_layout = QHBoxLayout()
        
        self.scan_btn = QPushButton("Start Scanner")
        self.scan_btn.clicked.connect(self.start_qr_scanner)
        controls_layout.addWidget(self.scan_btn)
        
        self.stop_scan_btn = QPushButton("Stop Scanner")
        self.stop_scan_btn.clicked.connect(self.stop_qr_scanner)
        self.stop_scan_btn.setEnabled(False)
        controls_layout.addWidget(self.stop_scan_btn)
        
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Status
        self.scanner_status = QLabel("Ready to scan")
        layout.addWidget(self.scanner_status)
        
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget
    
    def create_file_tab(self) -> QWidget:
        """Create file import tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel(
            "Import a recipe from a JSON file. The file should contain a valid recipe exported from the mobile app."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # File selection
        file_layout = QHBoxLayout()
        
        self.file_path_label = QLabel("No file selected")
        file_layout.addWidget(self.file_path_label, 1)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_recipe_file)
        file_layout.addWidget(browse_btn)
        
        layout.addLayout(file_layout)
        
        # Recent files
        recent_group = QGroupBox("Recent Recipes")
        recent_layout = QVBoxLayout()
        
        self.recent_files_combo = QComboBox()
        self.recent_files_combo.addItem("No recent recipes")
        recent_layout.addWidget(self.recent_files_combo)
        
        recent_group.setLayout(recent_layout)
        layout.addWidget(recent_group)
        
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget
    
    def create_manual_tab(self) -> QWidget:
        """Create manual paste tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel(
            "Paste recipe JSON directly. You can copy the JSON from:\n"
            "• Email attachments\n"
            "• Cloud storage (Google Drive, Dropbox, OneDrive)\n"
            "• Direct message from another user"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Paste area
        paste_label = QLabel("Paste recipe JSON here:")
        layout.addWidget(paste_label)
        
        self.paste_text = QTextEdit()
        self.paste_text.setPlaceholderText('{\n  "version": "1.0.0",\n  "name": "...",\n  ...\n}')
        layout.addWidget(self.paste_text)
        
        # Load button
        load_btn = QPushButton("Load from Paste")
        load_btn.clicked.connect(self.load_from_paste)
        layout.addWidget(load_btn)
        
        widget.setLayout(layout)
        return widget
    
    def start_qr_scanner(self):
        """Start QR code scanner"""
        self.scanner_status.setText("Starting camera...")
        self.scan_btn.setEnabled(False)
        self.stop_scan_btn.setEnabled(True)
        
        self.scanner_thread = QRCodeScannerThread()
        self.scanner_thread.qr_detected.connect(self.on_qr_detected)
        self.scanner_thread.error_occurred.connect(self.on_scanner_error)
        self.scanner_thread.start()
        
        self.scanner_status.setText("Camera active - point at QR code...")
    
    def stop_qr_scanner(self):
        """Stop QR code scanner"""
        if self.scanner_thread:
            self.scanner_thread.stop()
            self.scanner_thread.wait()
            self.scanner_thread = None
        
        self.scan_btn.setEnabled(True)
        self.stop_scan_btn.setEnabled(False)
        self.scanner_status.setText("Scanner stopped")
    
    def on_qr_detected(self, qr_data: str):
        """Handle QR code detection"""
        self.stop_qr_scanner()
        
        try:
            recipe = json.loads(qr_data)
            self.on_recipe_loaded(recipe)
            self.scanner_status.setText("✓ Recipe loaded from QR code")
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Invalid QR Code", f"QR code does not contain valid JSON:\n\n{str(e)}")
            self.scanner_status.setText("✗ Invalid QR code data")
    
    def on_scanner_error(self, error_msg: str):
        """Handle scanner error"""
        self.stop_qr_scanner()
        QMessageBox.critical(self, "Scanner Error", error_msg)
        self.scanner_status.setText("✗ Scanner error")
    
    def browse_recipe_file(self):
        """Browse for recipe file"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Select Recipe File", "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    recipe = json.load(f)
                self.file_path_label.setText(filename)
                self.on_recipe_loaded(recipe)
            except json.JSONDecodeError as e:
                QMessageBox.critical(self, "Invalid JSON", f"File does not contain valid JSON:\n\n{str(e)}")
            except Exception as e:
                QMessageBox.critical(self, "File Error", f"Failed to read file:\n\n{str(e)}")
    
    def load_from_paste(self):
        """Load recipe from pasted JSON"""
        json_text = self.paste_text.toPlainText().strip()
        
        if not json_text:
            QMessageBox.warning(self, "Empty Input", "Please paste recipe JSON first")
            return
        
        try:
            recipe = json.loads(json_text)
            self.on_recipe_loaded(recipe)
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Invalid JSON", f"Pasted text is not valid JSON:\n\n{str(e)}")
    
    def on_recipe_loaded(self, recipe: dict):
        """Handle recipe loaded"""
        self.current_recipe = recipe
        
        # Update preview
        preview_text = json.dumps(recipe, indent=2)[:500]  # First 500 chars
        self.recipe_text.setText(preview_text + "..." if len(json.dumps(recipe)) > 500 else preview_text)
        
        # Enable buttons
        self.clear_btn.setEnabled(True)
        self.validate_btn.setEnabled(True)
        
        # Emit signal
        self.recipe_loaded.emit(recipe)
        
        logger.info(f"Recipe loaded: {recipe.get('name', 'Unknown')}")
    
    def validate_recipe(self):
        """Validate current recipe"""
        if not self.current_recipe:
            QMessageBox.warning(self, "No Recipe", "Please load a recipe first")
            return
        
        # Check required fields
        required_fields = ['version', 'id', 'name', 'targetDevice', 'partitions']
        missing_fields = [f for f in required_fields if f not in self.current_recipe]
        
        if missing_fields:
            QMessageBox.warning(
                self, "Invalid Recipe",
                f"Recipe is missing required fields:\n\n{', '.join(missing_fields)}"
            )
            return
        
        QMessageBox.information(self, "Valid Recipe", "Recipe is valid and ready to use!")
    
    def clear_recipe(self):
        """Clear current recipe"""
        self.current_recipe = None
        self.recipe_text.clear()
        self.paste_text.clear()
        self.file_path_label.setText("No file selected")
        self.clear_btn.setEnabled(False)
        self.validate_btn.setEnabled(False)
    
    def set_recipe_text(self, text: str):
        """Set recipe text (for external loading)"""
        self.paste_text.setText(text)
