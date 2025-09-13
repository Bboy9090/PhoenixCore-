"""
BootForge Stepper Wizard Widget
Main stepper interface combining StepperHeader with step content for professional guided workflow
"""

import logging
from typing import Optional, Dict, Any, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QStackedWidget, QLabel, 
    QPushButton, QHBoxLayout, QSpacerItem, QSizePolicy,
    QGroupBox, QTextEdit, QProgressBar, QCheckBox,
    QComboBox, QListWidget, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPixmap

from src.gui.stepper_header import StepperHeader, StepState
from src.gui.stepper_wizard import WizardController, WizardStep, WizardState
from src.core.disk_manager import DiskManager


class StepView(QWidget):
    """Base class for individual step views in the wizard"""
    
    step_completed = pyqtSignal()
    step_data_changed = pyqtSignal(dict)
    request_next_step = pyqtSignal()
    request_previous_step = pyqtSignal()
    
    def __init__(self, step_title: str, step_description: str):
        super().__init__()
        self.step_title = step_title
        self.step_description = step_description
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the step view UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Step title and description
        title_label = QLabel(self.step_title)
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #ffffff; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        desc_label = QLabel(self.step_description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #cccccc; font-size: 14px; margin-bottom: 20px;")
        layout.addWidget(desc_label)
        
        # Content area for subclasses to customize
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.content_widget)
        
        # Navigation buttons area
        nav_layout = QHBoxLayout()
        nav_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        
        self.previous_button = QPushButton("Previous")
        self.previous_button.setMinimumSize(100, 35)
        self.previous_button.clicked.connect(self.request_previous_step)
        nav_layout.addWidget(self.previous_button)
        
        self.next_button = QPushButton("Next")
        self.next_button.setMinimumSize(100, 35)
        self.next_button.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QPushButton:disabled {
                background-color: #4a4a4a;
                color: #888888;
            }
        """)
        self.next_button.clicked.connect(self.request_next_step)
        nav_layout.addWidget(self.next_button)
        
        layout.addLayout(nav_layout)
        
        # Add spacer to push content up
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
    
    def set_navigation_enabled(self, previous: bool = True, next: bool = True):
        """Enable/disable navigation buttons"""
        self.previous_button.setEnabled(previous)
        self.next_button.setEnabled(next)
    
    def validate_step(self) -> bool:
        """Validate step data before proceeding - override in subclasses"""
        return True
    
    def get_step_data(self) -> Dict[str, Any]:
        """Get step data - override in subclasses"""
        return {}
    
    def load_step_data(self, data: Dict[str, Any]):
        """Load step data - override in subclasses"""
        pass
    
    def on_step_entered(self):
        """Called when step becomes active - override in subclasses"""
        pass
    
    def on_step_left(self):
        """Called when leaving step - override in subclasses"""
        pass


class HardwareDetectionStepView(StepView):
    """Hardware detection step view"""
    
    def __init__(self):
        super().__init__(
            "Hardware Detection",
            "Detecting your computer's hardware to recommend the best OS deployment configuration."
        )
        self._setup_content()
    
    def _setup_content(self):
        """Setup hardware detection content"""
        # Status group
        status_group = QGroupBox("Detection Status")
        status_layout = QVBoxLayout(status_group)
        
        self.status_label = QLabel("Ready to scan hardware...")
        self.status_label.setStyleSheet("color: #cccccc; font-size: 14px;")
        status_layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)
        
        # Start detection button
        self.scan_button = QPushButton("Start Hardware Detection")
        self.scan_button.setMinimumSize(200, 40)
        self.scan_button.clicked.connect(self._start_detection)
        status_layout.addWidget(self.scan_button)
        
        self.content_layout.addWidget(status_group)
        
        # Results area
        self.results_group = QGroupBox("Detected Hardware")
        results_layout = QVBoxLayout(self.results_group)
        
        self.results_text = QTextEdit()
        self.results_text.setMaximumHeight(200)
        self.results_text.setReadOnly(True)
        self.results_text.setStyleSheet("""
            QTextEdit {
                background-color: #2d2d30;
                color: #cccccc;
                border: 1px solid #555555;
                font-family: 'Courier New', monospace;
            }
        """)
        results_layout.addWidget(self.results_text)
        
        self.results_group.setVisible(False)
        self.content_layout.addWidget(self.results_group)
    
    def _start_detection(self):
        """Start hardware detection simulation"""
        self.scan_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Scanning hardware components...")
        
        # Simulate detection process
        self.detection_timer = QTimer()
        self.detection_timer.timeout.connect(self._update_detection)
        self.detection_timer.start(100)
        self.detection_progress = 0
    
    def _update_detection(self):
        """Update detection progress"""
        self.detection_progress += 5
        self.progress_bar.setValue(self.detection_progress)
        
        if self.detection_progress >= 100:
            self.detection_timer.stop()
            self._complete_detection()
    
    def _complete_detection(self):
        """Complete hardware detection"""
        self.status_label.setText("Hardware detection completed successfully!")
        self.results_group.setVisible(True)
        
        # Show mock detection results
        results = """CPU: Intel Core i7-10700K @ 3.80GHz
RAM: 32GB DDR4
Storage: NVMe SSD 1TB
GPU: NVIDIA GeForce RTX 3070
Motherboard: ASUS ROG STRIX Z490-E
Network: Intel Ethernet I225-V
Audio: Realtek ALC1220

Recommended Profile: High-Performance Gaming System
Compatible OS: macOS 12+, Windows 11, Linux (all distributions)"""
        
        self.results_text.setText(results)
        self.set_navigation_enabled(next=True)
        self.step_completed.emit()


class OSImageSelectionStepView(StepView):
    """OS image selection step view"""
    
    def __init__(self):
        super().__init__(
            "OS Image Selection",
            "Select the operating system image file to deploy to your USB drive."
        )
        self.selected_image_path = None
        self._setup_content()
    
    def _setup_content(self):
        """Setup OS image selection content"""
        # Image selection group
        selection_group = QGroupBox("Select OS Image")
        selection_layout = QVBoxLayout(selection_group)
        
        # Current selection display
        self.selection_label = QLabel("No image selected")
        self.selection_label.setStyleSheet("color: #cccccc; font-size: 14px; padding: 10px;")
        selection_layout.addWidget(self.selection_label)
        
        # Browse button
        browse_button = QPushButton("Browse for Image File...")
        browse_button.setMinimumSize(200, 40)
        browse_button.clicked.connect(self._browse_image)
        selection_layout.addWidget(browse_button)
        
        self.content_layout.addWidget(selection_group)
        
        # Image info group
        self.info_group = QGroupBox("Image Information")
        info_layout = QVBoxLayout(self.info_group)
        
        self.info_text = QTextEdit()
        self.info_text.setMaximumHeight(150)
        self.info_text.setReadOnly(True)
        info_layout.addWidget(self.info_text)
        
        self.info_group.setVisible(False)
        self.content_layout.addWidget(self.info_group)
    
    def _browse_image(self):
        """Browse for image file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select OS Image File",
            "",
            "Image Files (*.iso *.dmg *.img *.bin);;All Files (*)"
        )
        
        if file_path:
            self.selected_image_path = file_path
            self.selection_label.setText(f"Selected: {file_path}")
            
            # Show mock image info
            info = f"""File: {file_path}
Size: 4.2 GB
Type: macOS Installer (DMG)
Version: macOS Ventura 13.0
Architecture: x86_64 + ARM64 (Universal)
Checksum: SHA256 verified ✓"""
            
            self.info_text.setText(info)
            self.info_group.setVisible(True)
            self.set_navigation_enabled(next=True)
            self.step_completed.emit()


class USBConfigurationStepView(StepView):
    """USB configuration step view"""
    
    def __init__(self):
        super().__init__(
            "USB Configuration", 
            "Configure USB drive settings and deployment options."
        )
        self._setup_content()
    
    def _setup_content(self):
        """Setup USB configuration content"""
        # Device selection group
        device_group = QGroupBox("Target USB Device")
        device_layout = QVBoxLayout(device_group)
        
        self.device_combo = QComboBox()
        self.device_combo.addItem("USB Drive - SanDisk 32GB (E:)")
        self.device_combo.addItem("USB Drive - Kingston 64GB (F:)")
        self.device_combo.currentTextChanged.connect(self._device_changed)
        device_layout.addWidget(self.device_combo)
        
        self.content_layout.addWidget(device_group)
        
        # Configuration options
        config_group = QGroupBox("Configuration Options")
        config_layout = QVBoxLayout(config_group)
        
        self.format_checkbox = QCheckBox("Format drive before writing (recommended)")
        self.format_checkbox.setChecked(True)
        config_layout.addWidget(self.format_checkbox)
        
        self.verify_checkbox = QCheckBox("Verify written data")
        self.verify_checkbox.setChecked(True)
        config_layout.addWidget(self.verify_checkbox)
        
        self.eject_checkbox = QCheckBox("Safely eject drive when complete")
        self.eject_checkbox.setChecked(True)
        config_layout.addWidget(self.eject_checkbox)
        
        self.content_layout.addWidget(config_group)
        
        # Enable next by default
        self.set_navigation_enabled(next=True)
    
    def _device_changed(self):
        """Handle device selection change"""
        self.step_data_changed.emit({"selected_device": self.device_combo.currentText()})


class SafetyReviewStepView(StepView):
    """Safety review step view"""
    
    def __init__(self):
        super().__init__(
            "Safety Review",
            "Review all settings and confirm the deployment operation."
        )
        self._setup_content()
    
    def _setup_content(self):
        """Setup safety review content"""
        # Summary group
        summary_group = QGroupBox("Deployment Summary")
        summary_layout = QVBoxLayout(summary_group)
        
        summary_text = """Source Image: macOS Ventura 13.0 (4.2 GB)
Target Device: SanDisk 32GB USB Drive
Operation: Format + Write + Verify
Estimated Time: 15-20 minutes

⚠️  WARNING: All data on the target drive will be permanently erased!"""
        
        summary_label = QLabel(summary_text)
        summary_label.setWordWrap(True)
        summary_label.setStyleSheet("color: #cccccc; font-size: 14px; padding: 10px;")
        summary_layout.addWidget(summary_label)
        
        self.content_layout.addWidget(summary_group)
        
        # Confirmation checkboxes
        confirm_group = QGroupBox("Safety Confirmations")
        confirm_layout = QVBoxLayout(confirm_group)
        
        self.backup_checkbox = QCheckBox("I have backed up any important data on the target drive")
        confirm_layout.addWidget(self.backup_checkbox)
        
        self.understand_checkbox = QCheckBox("I understand that this operation cannot be undone")
        confirm_layout.addWidget(self.understand_checkbox)
        
        self.proceed_checkbox = QCheckBox("I am ready to proceed with the deployment")
        confirm_layout.addWidget(self.proceed_checkbox)
        
        # Connect checkboxes to validation
        for checkbox in [self.backup_checkbox, self.understand_checkbox, self.proceed_checkbox]:
            checkbox.toggled.connect(self._validate_confirmations)
        
        self.content_layout.addWidget(confirm_group)
        
        # Initially disable next
        self.set_navigation_enabled(next=False)
    
    def _validate_confirmations(self):
        """Validate safety confirmations"""
        all_checked = (self.backup_checkbox.isChecked() and 
                      self.understand_checkbox.isChecked() and 
                      self.proceed_checkbox.isChecked())
        self.set_navigation_enabled(next=all_checked)
        if all_checked:
            self.step_completed.emit()


class BuildVerifyStepView(StepView):
    """Build and verify step view"""
    
    def __init__(self):
        super().__init__(
            "Build & Verify",
            "Creating the bootable USB drive. Please do not disconnect the device."
        )
        self._setup_content()
    
    def _setup_content(self):
        """Setup build and verify content"""
        # Progress group
        progress_group = QGroupBox("Build Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.status_label = QLabel("Ready to start build process...")
        self.status_label.setStyleSheet("color: #cccccc; font-size: 14px;")
        progress_layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        
        self.details_label = QLabel("")
        self.details_label.setStyleSheet("color: #aaaaaa; font-size: 12px;")
        progress_layout.addWidget(self.details_label)
        
        self.content_layout.addWidget(progress_group)
        
        # Initially disable navigation
        self.set_navigation_enabled(previous=False, next=False)
    
    def on_step_entered(self):
        """Start build process when step is entered"""
        self._start_build()
    
    def _start_build(self):
        """Start the build process simulation"""
        self.status_label.setText("Starting build process...")
        self.progress_bar.setValue(0)
        
        self.build_timer = QTimer()
        self.build_timer.timeout.connect(self._update_build)
        self.build_timer.start(200)
        self.build_progress = 0
        self.build_stage = 0
        
        self.build_stages = [
            "Preparing USB drive...",
            "Formatting drive...",
            "Writing OS image...", 
            "Verifying written data...",
            "Finalizing installation..."
        ]
    
    def _update_build(self):
        """Update build progress"""
        self.build_progress += 2
        self.progress_bar.setValue(self.build_progress)
        
        # Update stage
        stage_progress = self.build_progress // 20
        if stage_progress < len(self.build_stages):
            self.details_label.setText(self.build_stages[stage_progress])
        
        if self.build_progress >= 100:
            self.build_timer.stop()
            self._complete_build()
    
    def _complete_build(self):
        """Complete the build process"""
        self.status_label.setText("Build completed successfully!")
        self.details_label.setText("USB drive is ready for use")
        self.set_navigation_enabled(previous=False, next=True)
        self.step_completed.emit()


class SummaryStepView(StepView):
    """Summary step view"""
    
    def __init__(self):
        super().__init__(
            "Summary",
            "Deployment completed successfully. Your bootable USB drive is ready."
        )
        self._setup_content()
    
    def _setup_content(self):
        """Setup summary content"""
        # Success message
        success_group = QGroupBox("Deployment Results")
        success_layout = QVBoxLayout(success_group)
        
        success_text = """✅ Bootable USB drive created successfully!

Operation Details:
• Source: macOS Ventura 13.0 (4.2 GB)
• Target: SanDisk 32GB USB Drive
• Duration: 18 minutes 34 seconds
• Verification: Passed ✓

Your USB drive is now ready to boot on compatible systems."""
        
        success_label = QLabel(success_text)
        success_label.setWordWrap(True)
        success_label.setStyleSheet("color: #cccccc; font-size: 14px; padding: 10px;")
        success_layout.addWidget(success_label)
        
        self.content_layout.addWidget(success_group)
        
        # Action buttons
        action_group = QGroupBox("Next Steps")
        action_layout = QVBoxLayout(action_group)
        
        eject_button = QPushButton("Safely Eject USB Drive")
        eject_button.clicked.connect(self._eject_drive)
        action_layout.addWidget(eject_button)
        
        new_button = QPushButton("Create Another USB Drive")
        new_button.clicked.connect(self._start_new)
        action_layout.addWidget(new_button)
        
        self.content_layout.addWidget(action_group)
        
        # Hide navigation buttons since we're at the end
        self.previous_button.setVisible(False)
        self.next_button.setText("Finish")
    
    def _eject_drive(self):
        """Safely eject the drive"""
        QMessageBox.information(self, "Success", "USB drive ejected safely.")
    
    def _start_new(self):
        """Start a new deployment"""
        self.request_previous_step.emit()  # This will need custom handling


class BootForgeStepperWizard(QWidget):
    """Main stepper wizard widget combining StepperHeader with step content"""
    
    # Signals for integration with main window
    wizard_completed = pyqtSignal()
    step_changed = pyqtSignal(int, str)  # step_index, step_name
    status_updated = pyqtSignal(str)  # status message
    progress_updated = pyqtSignal(int)  # progress percentage
    
    def __init__(self, disk_manager: DiskManager):
        super().__init__()
        self.disk_manager = disk_manager
        self.logger = logging.getLogger(__name__)
        
        # Initialize wizard controller (temporarily disabled for debugging)
        self.wizard_controller = None  # Temporarily disable controller
        
        # Setup UI
        self._setup_ui()
        self._setup_step_views()
        self._setup_connections()
        
        # Initialize to first step
        self._update_current_step(0)
        
        self.logger.info("BootForge stepper wizard initialized")
    
    def _setup_ui(self):
        """Setup the main wizard UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create stepper header
        step_names = [
            "Hardware Detection",
            "OS Image Selection", 
            "USB Configuration",
            "Safety Review",
            "Build & Verify",
            "Summary"
        ]
        
        self.stepper_header = StepperHeader()
        layout.addWidget(self.stepper_header)
        
        # Create stacked widget for step content
        self.step_stack = QStackedWidget()
        layout.addWidget(self.step_stack)
        
        self.current_step_index = 0
    
    def _setup_step_views(self):
        """Setup individual step view widgets"""
        self.step_views = [
            HardwareDetectionStepView(),
            OSImageSelectionStepView(),
            USBConfigurationStepView(),
            SafetyReviewStepView(),
            BuildVerifyStepView(),
            SummaryStepView()
        ]
        
        # Add step views to stack
        for step_view in self.step_views:
            self.step_stack.addWidget(step_view)
        
        # Connect step view signals
        for i, step_view in enumerate(self.step_views):
            step_view.step_completed.connect(lambda idx=i: self._on_step_completed(idx))
            step_view.step_data_changed.connect(lambda data, idx=i: self._on_step_data_changed(idx, data))
            step_view.request_next_step.connect(self._next_step)
            step_view.request_previous_step.connect(self._previous_step)
    
    def _setup_connections(self):
        """Setup signal connections"""
        # Connect stepper header navigation
        self.stepper_header.step_clicked.connect(self._navigate_to_step)
        
        # Connect wizard controller signals (if controller is available)
        if self.wizard_controller:
            self.wizard_controller.step_changed.connect(self._on_controller_step_changed)
            self.wizard_controller.state_updated.connect(self._on_controller_state_updated)
    
    def _update_current_step(self, step_index: int):
        """Update the current step"""
        if 0 <= step_index < len(self.step_views):
            # Update header
            self.stepper_header.set_current_step(step_index)
            
            # Update stack
            old_index = self.current_step_index
            self.current_step_index = step_index
            self.step_stack.setCurrentIndex(step_index)
            
            # Notify views
            if old_index != step_index:
                if 0 <= old_index < len(self.step_views):
                    self.step_views[old_index].on_step_left()
                self.step_views[step_index].on_step_entered()
            
            # Emit signals
            step_name = ["Hardware Detection", "OS Image Selection", "USB Configuration", 
                        "Safety Review", "Build & Verify", "Summary"][step_index]
            self.step_changed.emit(step_index, step_name)
            self.status_updated.emit(f"Step {step_index + 1}: {step_name}")
            
            self.logger.debug(f"Navigated to step {step_index}: {step_name}")
    
    def _navigate_to_step(self, step_index: int):
        """Navigate to specific step (from header click)"""
        # Only allow navigation to completed or adjacent steps
        if step_index <= self.current_step_index + 1:
            self._update_current_step(step_index)
    
    def _next_step(self):
        """Navigate to next step"""
        if self.current_step_index < len(self.step_views) - 1:
            current_view = self.step_views[self.current_step_index]
            if current_view.validate_step():
                self._update_current_step(self.current_step_index + 1)
                # Mark previous step as complete
                self.stepper_header.mark_step_complete(self.current_step_index - 1)
            else:
                self.status_updated.emit("Please complete the current step before proceeding")
    
    def _previous_step(self):
        """Navigate to previous step"""
        if self.current_step_index > 0:
            self._update_current_step(self.current_step_index - 1)
    
    def _on_step_completed(self, step_index: int):
        """Handle step completion"""
        self.stepper_header.mark_step_complete(step_index)
        self.status_updated.emit(f"Step {step_index + 1} completed successfully")
        
        # Auto-advance for certain steps
        if step_index == len(self.step_views) - 1:
            self.wizard_completed.emit()
    
    def _on_step_data_changed(self, step_index: int, data: Dict[str, Any]):
        """Handle step data changes"""
        self.logger.debug(f"Step {step_index} data changed: {data}")
    
    def _on_controller_step_changed(self, old_step, new_step):
        """Handle wizard controller step changes"""
        step_index = list(WizardStep).index(new_step)
        self._update_current_step(step_index)
    
    def _on_controller_state_updated(self, state: WizardState):
        """Handle wizard controller state updates"""
        self.logger.debug(f"Wizard state updated: {state.current_step}")
    
    def reset_wizard(self):
        """Reset wizard to initial state"""
        self._update_current_step(0)
        for i, step_view in enumerate(self.step_views):
            pass  # States will be handled by set_current_step
        self.stepper_header.set_current_step(0)
        self.status_updated.emit("Wizard reset to beginning")
        self.logger.info("Wizard reset to initial state")