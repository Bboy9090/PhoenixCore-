"""
BootForge StepperHeader Widget
Beautiful horizontal stepper component showing wizard progress through 6-step deployment workflow
"""

import logging
from enum import Enum, auto
from typing import Optional, List, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, 
    QFrame, QSizePolicy, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect, QTimer
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPixmap, QPalette, QIcon

from src.gui.stepper_wizard import WizardStep, WizardController


class StepState(Enum):
    """Visual states for stepper steps"""
    LOCKED = auto()      # Step not yet accessible (gray, disabled)
    ACTIVE = auto()      # Current step being worked on (blue, highlighted) 
    COMPLETE = auto()    # Successfully completed step (green, checkmark)
    ERROR = auto()       # Step has validation error (red, warning icon)


class StepIndicator(QWidget):
    """Individual step indicator widget with number/icon and connecting line"""
    
    clicked = pyqtSignal(int)  # Emits step index when clicked
    
    def __init__(self, step_index: int, step_name: str, is_last: bool = False):
        super().__init__()
        self.step_index = step_index
        self.step_name = step_name
        self.is_last = is_last
        self.state = StepState.LOCKED
        self._clickable = False
        
        # Styling constants
        self.CIRCLE_SIZE = 40
        self.LINE_WIDTH = 3
        self.LINE_LENGTH = 80
        
        # Colors for different states
        self.colors = {
            StepState.LOCKED: {
                'circle': '#4a4a4a',
                'text': '#888888',
                'line': '#333333'
            },
            StepState.ACTIVE: {
                'circle': '#0078d4',
                'text': '#ffffff',
                'line': '#0078d4'
            },
            StepState.COMPLETE: {
                'circle': '#107c10',
                'text': '#ffffff', 
                'line': '#107c10'
            },
            StepState.ERROR: {
                'circle': '#d13438',
                'text': '#ffffff',
                'line': '#d13438'
            }
        }
        
        self.setFixedSize(self.LINE_LENGTH + self.CIRCLE_SIZE if not is_last else self.CIRCLE_SIZE, 80)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Add subtle shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
        
        self.logger = logging.getLogger(f"{__name__}.StepIndicator")
    
    def set_state(self, state: StepState, clickable: bool = False):
        """Update step visual state and clickability"""
        state_changed = (self.state != state)
        clickable_changed = (self._clickable != clickable)
        
        if state_changed or clickable_changed:
            if state_changed:
                self.state = state
                self.logger.debug(f"Step {self.step_index} state changed to {state.name}")
            
            if clickable_changed:
                self._clickable = clickable
                # Update cursor based on clickability
                if clickable and self.state in [StepState.COMPLETE, StepState.ACTIVE]:
                    self.setCursor(Qt.CursorShape.PointingHandCursor)
                else:
                    self.setCursor(Qt.CursorShape.ArrowCursor)
                self.logger.debug(f"Step {self.step_index} clickability changed to {clickable}")
            
            self.update()  # Trigger repaint when any property changes
    
    def is_clickable(self) -> bool:
        """Check if step is clickable"""
        return self._clickable
    
    def mousePressEvent(self, a0):
        """Handle mouse clicks"""
        if a0 and a0.button() == Qt.MouseButton.LeftButton and self.is_clickable():
            self.clicked.emit(self.step_index)
            self.logger.debug(f"Step {self.step_index} clicked")
        super().mousePressEvent(a0)
    
    def paintEvent(self, a0):
        """Custom paint method for step visualization"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Get colors for current state
        color_scheme = self.colors[self.state]
        circle_color = QColor(color_scheme['circle'])
        text_color = QColor(color_scheme['text'])
        line_color = QColor(color_scheme['line'])
        
        # Draw connecting line (if not last step)
        if not self.is_last:
            line_y = self.height() // 2
            line_start_x = self.CIRCLE_SIZE + 5
            line_end_x = self.width() - 5
            
            pen = QPen(line_color, self.LINE_WIDTH)
            painter.setPen(pen)
            painter.drawLine(line_start_x, line_y, line_end_x, line_y)
        
        # Draw step circle
        circle_x = 0
        circle_y = (self.height() - self.CIRCLE_SIZE) // 2
        circle_rect = QRect(circle_x, circle_y, self.CIRCLE_SIZE, self.CIRCLE_SIZE)
        
        # Add hover effect for clickable steps
        if self.is_clickable() and self.underMouse():
            # Draw slightly larger circle for hover effect
            hover_rect = QRect(circle_x - 2, circle_y - 2, self.CIRCLE_SIZE + 4, self.CIRCLE_SIZE + 4)
            painter.setBrush(QBrush(circle_color.lighter(120)))
            painter.setPen(QPen(circle_color.lighter(140), 2))
            painter.drawEllipse(hover_rect)
        
        # Main circle
        painter.setBrush(QBrush(circle_color))
        painter.setPen(QPen(circle_color.darker(110), 2))
        painter.drawEllipse(circle_rect)
        
        # Draw step content (number or icon)
        painter.setPen(QPen(text_color))
        
        if self.state == StepState.COMPLETE:
            # Draw checkmark
            font = QFont("Arial", 14, QFont.Weight.Bold)
            painter.setFont(font)
            painter.drawText(circle_rect, Qt.AlignmentFlag.AlignCenter, "✓")
        elif self.state == StepState.ERROR:
            # Draw warning icon
            font = QFont("Arial", 14, QFont.Weight.Bold)
            painter.setFont(font)
            painter.drawText(circle_rect, Qt.AlignmentFlag.AlignCenter, "!")
        else:
            # Draw step number
            font = QFont("Arial", 12, QFont.Weight.Bold)
            painter.setFont(font)
            painter.drawText(circle_rect, Qt.AlignmentFlag.AlignCenter, str(self.step_index + 1))
        
        # Draw step name below circle
        name_rect = QRect(circle_x - 20, circle_y + self.CIRCLE_SIZE + 5, self.CIRCLE_SIZE + 40, 20)
        font = QFont("Arial", 9)
        painter.setFont(font)
        
        # Adjust text color based on state
        if self.state == StepState.LOCKED:
            painter.setPen(QPen(QColor('#888888')))
        else:
            painter.setPen(QPen(QColor('#ffffff')))
        
        painter.drawText(name_rect, Qt.AlignmentFlag.AlignCenter, self.step_name)


class StepperHeader(QWidget):
    """
    Beautiful horizontal stepper header showing progress through 6-step deployment workflow
    
    Features:
    - Visual progress indication with different states
    - Click-back navigation to completed steps
    - Professional styling with animations
    - Integration with WizardController signals
    """
    
    step_clicked = pyqtSignal(int)  # Emitted when user clicks a step
    
    def __init__(self, wizard_controller: Optional[WizardController] = None):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.wizard_controller = wizard_controller
        
        # Step definitions
        self.step_names = [
            "Detect Hardware",
            "Select OS Image", 
            "Configure USB",
            "Safety Review",
            "Build & Verify",
            "Summary"
        ]
        
        # State tracking
        self.current_step_index = 0
        self.step_states: List[StepState] = [StepState.LOCKED] * len(self.step_names)
        self.step_states[0] = StepState.ACTIVE  # Start with first step active
        
        # UI components
        self.step_indicators: List[StepIndicator] = []
        
        self._setup_ui()
        self._setup_connections()
        
        # Initialize visual state and progress label
        self._update_step_states()
        self._update_progress_label()
        
        self.logger.info("StepperHeader initialized with 6 steps")
    
    def _setup_ui(self):
        """Setup the stepper header UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)
        
        # Title section
        title_layout = QHBoxLayout()
        
        title_label = QLabel("Deployment Workflow")
        title_font = QFont("Arial", 14, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #ffffff;")
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        # Progress percentage
        self.progress_label = QLabel("Step 1 of 6")
        self.progress_label.setStyleSheet("color: #cccccc; font-size: 12px;")
        title_layout.addWidget(self.progress_label)
        
        layout.addLayout(title_layout)
        
        # Stepper indicators section
        stepper_layout = QHBoxLayout()
        stepper_layout.setContentsMargins(0, 10, 0, 0)
        stepper_layout.setSpacing(0)
        
        # Create step indicators
        for i, step_name in enumerate(self.step_names):
            is_last = (i == len(self.step_names) - 1)
            step_indicator = StepIndicator(i, step_name, is_last)
            step_indicator.clicked.connect(self._on_step_clicked)
            
            self.step_indicators.append(step_indicator)
            stepper_layout.addWidget(step_indicator)
            
            if not is_last:
                stepper_layout.addStretch()
        
        layout.addLayout(stepper_layout)
        
        # Apply styling
        self._apply_styling()
    
    def _apply_styling(self):
        """Apply professional styling to the stepper header"""
        self.setStyleSheet("""
            StepperHeader {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #3c3c3c, stop:1 #2b2b2b);
                border: 1px solid #555555;
                border-radius: 8px;
                margin: 5px;
            }
        """)
        
        # Set fixed height for consistent layout
        self.setFixedHeight(120)
    
    def _setup_connections(self):
        """Setup signal connections with WizardController"""
        if self.wizard_controller:
            # Listen for step changes
            self.wizard_controller.step_changed.connect(self._on_wizard_step_changed)
            
            # Listen for validation failures
            self.wizard_controller.validation_failed.connect(self._on_validation_failed)
            
            # Connect our step clicks to wizard controller
            self.step_clicked.connect(self._on_step_navigation_requested)
            
            self.logger.debug("Connected to WizardController signals")
    
    def set_current_step(self, step_index: int):
        """Set the current active step"""
        if 0 <= step_index < len(self.step_names):
            old_index = self.current_step_index
            self.current_step_index = step_index
            
            # Update step states
            self._update_step_states()
            self._update_progress_label()
            
            self.logger.info(f"Current step changed from {old_index} to {step_index}")
    
    def mark_step_complete(self, step_index: int):
        """Mark a step as completed"""
        if 0 <= step_index < len(self.step_names):
            self.step_states[step_index] = StepState.COMPLETE
            self.step_indicators[step_index].set_state(StepState.COMPLETE, clickable=True)
            self.logger.debug(f"Step {step_index} marked as complete")
    
    def mark_step_error(self, step_index: int):
        """Mark a step as having an error"""
        if 0 <= step_index < len(self.step_names):
            self.step_states[step_index] = StepState.ERROR
            self.step_indicators[step_index].set_state(StepState.ERROR, clickable=True)
            self.logger.warning(f"Step {step_index} marked as error")
    
    def _update_step_states(self):
        """Update visual states of all step indicators"""
        for i, indicator in enumerate(self.step_indicators):
            if i < self.current_step_index:
                # Previous steps should be complete
                if self.step_states[i] != StepState.ERROR:
                    self.step_states[i] = StepState.COMPLETE
                indicator.set_state(self.step_states[i], clickable=True)
            elif i == self.current_step_index:
                # Current step is active
                if self.step_states[i] != StepState.ERROR:
                    self.step_states[i] = StepState.ACTIVE
                indicator.set_state(self.step_states[i], clickable=True)
            else:
                # Future steps are locked
                self.step_states[i] = StepState.LOCKED
                indicator.set_state(StepState.LOCKED, clickable=False)
    
    def _update_progress_label(self):
        """Update the progress label text"""
        step_name = self.step_names[self.current_step_index]
        self.progress_label.setText(f"Step {self.current_step_index + 1} of {len(self.step_names)}: {step_name}")
    
    def _on_step_clicked(self, step_index: int):
        """Handle step indicator clicks with enhanced navigation guards"""
        # Validate step index bounds
        if not (0 <= step_index < len(self.step_names)):
            self.logger.warning(f"Step {step_index} click ignored - invalid index")
            return
        
        # Enhanced navigation guards
        step_state = self.step_states[step_index]
        is_completed_step = step_state == StepState.COMPLETE
        is_current_step = (step_index == self.current_step_index and step_state == StepState.ACTIVE)
        is_accessible = step_index <= self.current_step_index
        
        # Only allow navigation to:
        # 1. Completed steps (can go back to review)
        # 2. Current active step (refresh current step)
        # 3. Steps that aren't in error state (unless it's current step)
        can_navigate = (
            is_accessible and 
            (is_completed_step or is_current_step) and
            (step_state != StepState.ERROR or is_current_step)
        )
        
        if can_navigate:
            self.step_clicked.emit(step_index)
            self.logger.info(f"Step navigation requested to step {step_index} (state: {step_state.name})")
        else:
            self.logger.debug(f"Step {step_index} click ignored - not accessible (state: {step_state.name}, current: {self.current_step_index})")
    
    def _on_step_navigation_requested(self, step_index: int):
        """Handle step navigation requests"""
        if self.wizard_controller:
            try:
                current_index = self.current_step_index
                
                if step_index < current_index:
                    # Navigate backward using back() method
                    steps_to_go_back = current_index - step_index
                    for _ in range(steps_to_go_back):
                        if not self.wizard_controller.back():
                            self.logger.warning(f"Failed to navigate back to step {step_index}")
                            break
                    self.logger.info(f"Navigated back from step {current_index} to step {step_index}")
                elif step_index == current_index:
                    # Stay on current step - just refresh UI
                    self.logger.debug(f"Staying on current step {step_index}")
                else:
                    # Forward navigation not allowed for step clicking
                    self.logger.warning(f"Forward navigation to step {step_index} not allowed via step clicking")
                    
            except Exception as e:
                self.logger.error(f"Failed to navigate to step {step_index}: {e}")
        else:
            self.logger.warning(f"No wizard controller available for step {step_index}")
    
    def _on_wizard_step_changed(self, old_step, new_step):
        """Handle wizard step changes from controller"""
        if hasattr(new_step, 'value'):
            # Convert WizardStep enum to index
            step_index = list(WizardStep).index(new_step)
            self.set_current_step(step_index)
        else:
            self.logger.warning(f"Received unknown step type: {new_step}")
    
    def _on_validation_failed(self, step_name: str, error_message: str):
        """Handle validation failure signals"""
        # Find step index by name and mark as error
        for i, name in enumerate(self.step_names):
            if step_name.lower() in name.lower():
                self.mark_step_error(i)
                self.logger.error(f"Validation failed for {step_name}: {error_message}")
                break
    
    def get_current_step_index(self) -> int:
        """Get the current step index"""
        return self.current_step_index
    
    def get_step_states(self) -> List[StepState]:
        """Get current states of all steps"""
        return self.step_states.copy()
    
    def reset_to_beginning(self):
        """Reset stepper to the beginning"""
        self.current_step_index = 0
        self.step_states = [StepState.LOCKED] * len(self.step_names)
        self.step_states[0] = StepState.ACTIVE
        self._update_step_states()
        self._update_progress_label()
        self.logger.info("StepperHeader reset to beginning")


# Utility function for creating stepper header
def create_stepper_header(wizard_controller: Optional[WizardController] = None) -> StepperHeader:
    """
    Factory function to create a properly configured StepperHeader
    
    Args:
        wizard_controller: Optional WizardController for integration
        
    Returns:
        Configured StepperHeader widget
    """
    return StepperHeader(wizard_controller)