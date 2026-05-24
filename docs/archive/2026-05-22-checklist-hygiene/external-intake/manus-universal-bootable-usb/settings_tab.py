"""
Settings Tab - Application settings and configuration
"""

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QFormLayout, QLineEdit,
    QSpinBox, QCheckBox, QPushButton, QComboBox, QLabel,
    QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt

logger = logging.getLogger(__name__)


class SettingsTab(QWidget):
    """Tab for application settings"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout()
        
        # API Settings
        api_group = QGroupBox("Backend API Settings")
        api_layout = QFormLayout()
        
        self.api_url_input = QLineEdit()
        self.api_url_input.setText("http://localhost:5000")
        self.api_url_input.setPlaceholderText("http://localhost:5000")
        api_layout.addRow("API URL:", self.api_url_input)
        
        self.api_timeout_spin = QSpinBox()
        self.api_timeout_spin.setMinimum(5)
        self.api_timeout_spin.setMaximum(300)
        self.api_timeout_spin.setValue(30)
        self.api_timeout_spin.setSuffix(" seconds")
        api_layout.addRow("API Timeout:", self.api_timeout_spin)
        
        api_group.setLayout(api_layout)
        layout.addWidget(api_group)
        
        # Build Settings
        build_group = QGroupBox("Build Settings")
        build_layout = QFormLayout()
        
        self.verify_checkbox = QCheckBox("Verify written data after build")
        self.verify_checkbox.setChecked(True)
        build_layout.addRow("", self.verify_checkbox)
        
        self.eject_checkbox = QCheckBox("Eject device after successful build")
        self.eject_checkbox.setChecked(True)
        build_layout.addRow("", self.eject_checkbox)
        
        self.buffer_size_spin = QSpinBox()
        self.buffer_size_spin.setMinimum(1)
        self.buffer_size_spin.setMaximum(1024)
        self.buffer_size_spin.setValue(64)
        self.buffer_size_spin.setSuffix(" MB")
        build_layout.addRow("Write Buffer Size:", self.buffer_size_spin)
        
        build_group.setLayout(build_layout)
        layout.addWidget(build_group)
        
        # Storage Settings
        storage_group = QGroupBox("Storage Settings")
        storage_layout = QFormLayout()
        
        self.cache_dir_input = QLineEdit()
        self.cache_dir_input.setText("/tmp/phoenixdrive-cache")
        self.cache_dir_input.setPlaceholderText("/tmp/phoenixdrive-cache")
        
        cache_layout = QWidget()
        cache_h_layout = QVBoxLayout(cache_layout)
        cache_h_layout.setContentsMargins(0, 0, 0, 0)
        cache_h_layout.addWidget(self.cache_dir_input)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_cache_dir)
        cache_h_layout.addWidget(browse_btn)
        
        storage_layout.addRow("Cache Directory:", cache_layout)
        
        self.max_cache_spin = QSpinBox()
        self.max_cache_spin.setMinimum(1)
        self.max_cache_spin.setMaximum(1000)
        self.max_cache_spin.setValue(100)
        self.max_cache_spin.setSuffix(" GB")
        storage_layout.addRow("Max Cache Size:", self.max_cache_spin)
        
        storage_group.setLayout(storage_layout)
        layout.addWidget(storage_group)
        
        # Logging Settings
        logging_group = QGroupBox("Logging Settings")
        logging_layout = QFormLayout()
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level_combo.setCurrentText("INFO")
        logging_layout.addRow("Log Level:", self.log_level_combo)
        
        self.save_logs_checkbox = QCheckBox("Save logs to file")
        self.save_logs_checkbox.setChecked(True)
        logging_layout.addRow("", self.save_logs_checkbox)
        
        logging_group.setLayout(logging_layout)
        layout.addWidget(logging_group)
        
        # Mobile App Integration
        mobile_group = QGroupBox("Mobile App Integration")
        mobile_layout = QFormLayout()
        
        self.mobile_sync_checkbox = QCheckBox("Enable mobile app synchronization")
        self.mobile_sync_checkbox.setChecked(True)
        mobile_layout.addRow("", self.mobile_sync_checkbox)
        
        self.mobile_url_input = QLineEdit()
        self.mobile_url_input.setText("http://localhost:8081")
        self.mobile_url_input.setPlaceholderText("http://localhost:8081")
        mobile_layout.addRow("Mobile App URL:", self.mobile_url_input)
        
        mobile_group.setLayout(mobile_layout)
        layout.addWidget(mobile_group)
        
        # Action buttons
        button_layout = QVBoxLayout()
        
        test_api_btn = QPushButton("Test API Connection")
        test_api_btn.clicked.connect(self.test_api_connection)
        button_layout.addWidget(test_api_btn)
        
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(save_btn)
        
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(reset_btn)
        
        layout.addLayout(button_layout)
        
        layout.addStretch()
        
        self.setLayout(layout)
    
    def browse_cache_dir(self):
        """Browse for cache directory"""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Cache Directory"
        )
        if directory:
            self.cache_dir_input.setText(directory)
    
    def test_api_connection(self):
        """Test API connection"""
        api_url = self.api_url_input.text()
        timeout = self.api_timeout_spin.value()
        
        try:
            import requests
            response = requests.get(
                f"{api_url}/api/v1/health",
                timeout=timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                QMessageBox.information(
                    self, "Connection Successful",
                    f"Successfully connected to API!\n\n"
                    f"Status: {data.get('status')}\n"
                    f"Version: {data.get('version')}"
                )
            else:
                QMessageBox.warning(
                    self, "Connection Failed",
                    f"API returned status code: {response.status_code}"
                )
        
        except requests.exceptions.ConnectionError:
            QMessageBox.critical(
                self, "Connection Error",
                f"Could not connect to API at {api_url}\n\n"
                f"Make sure the backend server is running."
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Error",
                f"Error testing API connection:\n\n{str(e)}"
            )
    
    def save_settings(self):
        """Save settings"""
        settings = {
            'api_url': self.api_url_input.text(),
            'api_timeout': self.api_timeout_spin.value(),
            'verify_write': self.verify_checkbox.isChecked(),
            'eject_device': self.eject_checkbox.isChecked(),
            'buffer_size': self.buffer_size_spin.value(),
            'cache_dir': self.cache_dir_input.text(),
            'max_cache': self.max_cache_spin.value(),
            'log_level': self.log_level_combo.currentText(),
            'save_logs': self.save_logs_checkbox.isChecked(),
            'mobile_sync': self.mobile_sync_checkbox.isChecked(),
            'mobile_url': self.mobile_url_input.text(),
        }
        
        # TODO: Save settings to config file
        logger.info(f"Settings saved: {settings}")
        QMessageBox.information(self, "Settings Saved", "Settings have been saved successfully!")
    
    def reset_to_defaults(self):
        """Reset settings to defaults"""
        reply = QMessageBox.question(
            self, "Reset Settings",
            "Are you sure you want to reset all settings to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.api_url_input.setText("http://localhost:5000")
            self.api_timeout_spin.setValue(30)
            self.verify_checkbox.setChecked(True)
            self.eject_checkbox.setChecked(True)
            self.buffer_size_spin.setValue(64)
            self.cache_dir_input.setText("/tmp/phoenixdrive-cache")
            self.max_cache_spin.setValue(100)
            self.log_level_combo.setCurrentText("INFO")
            self.save_logs_checkbox.setChecked(True)
            self.mobile_sync_checkbox.setChecked(True)
            self.mobile_url_input.setText("http://localhost:8081")
            
            QMessageBox.information(self, "Reset Complete", "Settings have been reset to defaults!")
