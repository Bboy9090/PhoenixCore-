"""
Build Progress Tab - Display real-time build progress
"""

import logging
from typing import Dict

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QProgressBar, QTextEdit, QGroupBox, QTableWidget, QTableWidgetItem
)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QFont, QColor

logger = logging.getLogger(__name__)


class BuildProgressTab(QWidget):
    """Tab for displaying build progress"""
    
    build_cancelled = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Build Progress")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Overall progress
        progress_group = QGroupBox("Overall Progress")
        progress_layout = QVBoxLayout()
        
        self.overall_progress_bar = QProgressBar()
        self.overall_progress_bar.setMinimum(0)
        self.overall_progress_bar.setMaximum(100)
        self.overall_progress_bar.setValue(0)
        progress_layout.addWidget(self.overall_progress_bar)
        
        self.overall_label = QLabel("Ready to start")
        progress_layout.addWidget(self.overall_label)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        # Stage progress
        stage_group = QGroupBox("Current Stage")
        stage_layout = QVBoxLayout()
        
        self.stage_label = QLabel("Waiting to start...")
        stage_layout.addWidget(self.stage_label)
        
        self.stage_progress_bar = QProgressBar()
        self.stage_progress_bar.setMinimum(0)
        self.stage_progress_bar.setMaximum(100)
        self.stage_progress_bar.setValue(0)
        stage_layout.addWidget(self.stage_progress_bar)
        
        stage_group.setLayout(stage_layout)
        layout.addWidget(stage_group)
        
        # Statistics
        stats_group = QGroupBox("Statistics")
        stats_layout = QVBoxLayout()
        
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(2)
        self.stats_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.stats_table.setMaximumHeight(150)
        
        # Add rows
        stats = [
            ("Speed", "-- MB/s"),
            ("Time Elapsed", "00:00:00"),
            ("Time Remaining", "-- --"),
            ("Data Written", "0 GB / 0 GB"),
        ]
        
        self.stats_table.setRowCount(len(stats))
        for i, (metric, value) in enumerate(stats):
            self.stats_table.setItem(i, 0, QTableWidgetItem(metric))
            self.stats_table.setItem(i, 1, QTableWidgetItem(value))
        
        stats_layout.addWidget(self.stats_table)
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # Log output
        log_group = QGroupBox("Build Log")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.clicked.connect(self.pause_build)
        self.pause_btn.setEnabled(False)
        button_layout.addWidget(self.pause_btn)
        
        self.resume_btn = QPushButton("Resume")
        self.resume_btn.clicked.connect(self.resume_build)
        self.resume_btn.setEnabled(False)
        button_layout.addWidget(self.resume_btn)
        
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel Build")
        self.cancel_btn.clicked.connect(self.cancel_build)
        self.cancel_btn.setEnabled(False)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def update_progress(self, progress_data: Dict):
        """Update progress display"""
        progress_type = progress_data.get('type', 'progress')
        
        if progress_type == 'progress':
            # Update overall progress
            overall = progress_data.get('overall_progress', 0)
            self.overall_progress_bar.setValue(int(overall))
            self.overall_label.setText(f"{overall:.1f}% Complete")
            
            # Update stage progress
            stage = progress_data.get('stage', 'Unknown')
            stage_progress = progress_data.get('stage_progress', 0)
            self.stage_label.setText(f"Stage: {stage}")
            self.stage_progress_bar.setValue(int(stage_progress))
            
            # Update statistics
            speed = progress_data.get('speed_mbps', 0)
            elapsed = progress_data.get('elapsed_time', '00:00:00')
            remaining = progress_data.get('eta_time', '--:--:--')
            written = progress_data.get('data_written', '0 GB')
            
            self.stats_table.item(0, 1).setText(f"{speed:.1f} MB/s")
            self.stats_table.item(1, 1).setText(elapsed)
            self.stats_table.item(2, 1).setText(remaining)
            self.stats_table.item(3, 1).setText(written)
            
            # Add to log
            message = progress_data.get('message', '')
            if message:
                self.log_text.append(f"[{stage}] {message}")
            
            # Enable cancel button
            self.cancel_btn.setEnabled(True)
        
        elif progress_type == 'completed':
            self.overall_progress_bar.setValue(100)
            self.overall_label.setText("Build Completed Successfully!")
            self.stage_label.setText("✓ Build Complete")
            self.log_text.append("\n✓ Build completed successfully!")
            
            self.cancel_btn.setEnabled(False)
            self.pause_btn.setEnabled(False)
            self.resume_btn.setEnabled(False)
        
        elif progress_type == 'error':
            error_msg = progress_data.get('message', 'Unknown error')
            self.overall_label.setText(f"✗ Build Failed: {error_msg}")
            self.log_text.append(f"\n✗ ERROR: {error_msg}")
            
            self.cancel_btn.setEnabled(False)
            self.pause_btn.setEnabled(False)
            self.resume_btn.setEnabled(False)
    
    def pause_build(self):
        """Pause build"""
        self.pause_btn.setEnabled(False)
        self.resume_btn.setEnabled(True)
        self.log_text.append("\n[PAUSED] Build paused by user")
    
    def resume_build(self):
        """Resume build"""
        self.pause_btn.setEnabled(True)
        self.resume_btn.setEnabled(False)
        self.log_text.append("\n[RESUMED] Build resumed")
    
    def cancel_build(self):
        """Cancel build"""
        self.log_text.append("\n[CANCELLED] Build cancelled by user")
        self.cancel_btn.setEnabled(False)
        self.pause_btn.setEnabled(False)
        self.resume_btn.setEnabled(False)
        self.build_cancelled.emit()
    
    def reset(self):
        """Reset progress display"""
        self.overall_progress_bar.setValue(0)
        self.stage_progress_bar.setValue(0)
        self.overall_label.setText("Ready to start")
        self.stage_label.setText("Waiting to start...")
        self.log_text.clear()
        
        # Reset stats
        for i in range(self.stats_table.rowCount()):
            self.stats_table.item(i, 1).setText("--")
        
        self.cancel_btn.setEnabled(False)
        self.pause_btn.setEnabled(False)
        self.resume_btn.setEnabled(False)
