"""
Arcwyre Control Center — Dashboard Module
The main hub showing system overview with real data.
Every metric comes from psutil — no mock values.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame,
    QScrollArea,
)
from PyQt6.QtCore import QTimer, Qt

from arcwyre.services import system_info
from arcwyre.widgets.status_card import StatusCard, InfoRow, SectionHeader
from arcwyre.theme import COLORS


class ControlCenterModule(QWidget):
    """Main dashboard showing system overview with real-time data."""

    MODULE_ID = "control_center"
    MODULE_TITLE = "Control Center"
    MODULE_SUBTITLE = "System Overview & Quick Actions"
    MODULE_ICON = "🏠"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._start_updates()

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # ── System Identity ────────────────────────────────────────────
        identity_frame = QFrame()
        identity_frame.setObjectName("card_highlight")
        identity_layout = QHBoxLayout(identity_frame)
        identity_layout.setContentsMargins(20, 16, 20, 16)

        identity_left = QVBoxLayout()
        self._hostname_label = QLabel("Loading...")
        self._hostname_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {COLORS['primary']};")
        identity_left.addWidget(self._hostname_label)

        self._os_label = QLabel("Detecting...")
        self._os_label.setStyleSheet(f"font-size: 12px; color: {COLORS['text_secondary']};")
        identity_left.addWidget(self._os_label)
        identity_layout.addLayout(identity_left, stretch=1)

        identity_right = QVBoxLayout()
        identity_right.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._uptime_label = QLabel("—")
        self._uptime_label.setStyleSheet(f"""
            font-family: monospace; font-size: 13px; color: {COLORS['success']};
            background-color: {COLORS['surface']}; padding: 6px 12px;
            border-radius: 6px; border: 1px solid {COLORS['border']};
        """)
        identity_right.addWidget(self._uptime_label)
        self._arch_label = QLabel("—")
        self._arch_label.setStyleSheet(f"font-size: 11px; color: {COLORS['text_tertiary']}; font-family: monospace;")
        identity_right.addWidget(self._arch_label, alignment=Qt.AlignmentFlag.AlignRight)
        identity_layout.addLayout(identity_right)

        layout.addWidget(identity_frame)

        # ── Quick Metrics Grid ─────────────────────────────────────────
        layout.addWidget(SectionHeader("System Metrics"))

        metrics_grid = QGridLayout()
        metrics_grid.setSpacing(12)

        self._cpu_card = StatusCard("CPU Usage", "—", "%", theme_color=COLORS['metric_cpu'])
        self._ram_card = StatusCard("Memory Usage", "—", "%", theme_color=COLORS['metric_ram'])
        self._disk_card = StatusCard("Primary Disk", "—", "%", theme_color=COLORS['metric_disk'])
        self._swap_card = StatusCard("Swap Usage", "—", "%", theme_color=COLORS['metric_temp'])

        metrics_grid.addWidget(self._cpu_card, 0, 0)
        metrics_grid.addWidget(self._ram_card, 0, 1)
        metrics_grid.addWidget(self._disk_card, 1, 0)
        metrics_grid.addWidget(self._swap_card, 1, 1)

        layout.addLayout(metrics_grid)

        # ── CPU Details ────────────────────────────────────────────────
        layout.addWidget(SectionHeader("Processor"))

        cpu_frame = QFrame()
        cpu_frame.setObjectName("card")
        cpu_layout = QVBoxLayout(cpu_frame)

        self._cpu_model_row = InfoRow("Model", "Detecting...")
        self._cpu_cores_row = InfoRow("Cores", "—")
        self._cpu_freq_row = InfoRow("Frequency", "—")

        cpu_layout.addWidget(self._cpu_model_row)
        cpu_layout.addWidget(self._cpu_cores_row)
        cpu_layout.addWidget(self._cpu_freq_row)
        layout.addWidget(cpu_frame)

        # ── Memory Details ─────────────────────────────────────────────
        layout.addWidget(SectionHeader("Memory"))

        mem_frame = QFrame()
        mem_frame.setObjectName("card")
        mem_layout = QVBoxLayout(mem_frame)

        self._mem_total_row = InfoRow("Total RAM", "—")
        self._mem_used_row = InfoRow("Used", "—")
        self._mem_available_row = InfoRow("Available", "—")

        mem_layout.addWidget(self._mem_total_row)
        mem_layout.addWidget(self._mem_used_row)
        mem_layout.addWidget(self._mem_available_row)
        layout.addWidget(mem_frame)

        # ── Disk Overview ──────────────────────────────────────────────
        layout.addWidget(SectionHeader("Storage"))
        self._disk_container = QVBoxLayout()
        layout.addLayout(self._disk_container)

        # ── Network Summary ────────────────────────────────────────────
        layout.addWidget(SectionHeader("Network Interfaces"))
        self._network_container = QVBoxLayout()
        layout.addLayout(self._network_container)

        layout.addStretch()

        scroll.setWidget(content)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def _start_updates(self):
        """Start real-time data polling."""
        self._update_data()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_data)
        self._timer.start(3000)  # Update every 3 seconds

    def _update_data(self):
        """Fetch real system data and update all cards."""
        try:
            # Hostname + OS
            hostname = system_info.get_hostname()
            self._hostname_label.setText(hostname)

            os_info = system_info.get_os_info()
            self._os_label.setText(f"{os_info['system']} {os_info['release']}")
            self._arch_label.setText(os_info['machine'])

            # Uptime
            uptime = system_info.get_uptime_seconds()
            self._uptime_label.setText(f"⏱  {system_info.format_uptime(uptime)}")

            # CPU
            cpu = system_info.get_cpu_info()
            cpu_pct = cpu['total_usage_percent']
            cpu_status = "ok" if cpu_pct < 70 else ("warning" if cpu_pct < 90 else "error")
            self._cpu_card.set_value(f"{cpu_pct:.1f}", cpu_status)
            self._cpu_model_row.set_value(cpu['model'])
            self._cpu_cores_row.set_value(f"{cpu['physical_cores']} physical, {cpu['logical_cores']} logical")
            freq = cpu['current_freq_mhz']
            if freq:
                self._cpu_freq_row.set_value(f"{freq:.0f} MHz")
            else:
                self._cpu_freq_row.set_value("Not available")

            # Memory
            mem = system_info.get_memory_info()
            mem_pct = mem['usage_percent']
            mem_status = "ok" if mem_pct < 70 else ("warning" if mem_pct < 90 else "error")
            self._ram_card.set_value(f"{mem_pct:.1f}", mem_status)
            self._mem_total_row.set_value(system_info.format_bytes(mem['total_bytes']))
            self._mem_used_row.set_value(system_info.format_bytes(mem['used_bytes']))
            self._mem_available_row.set_value(system_info.format_bytes(mem['available_bytes']))

            # Swap
            swap_pct = mem['swap_percent']
            swap_status = "ok" if swap_pct < 50 else ("warning" if swap_pct < 80 else "error")
            self._swap_card.set_value(f"{swap_pct:.1f}", swap_status)

            # Disks
            disks = system_info.get_disk_info()
            if disks:
                primary = disks[0]
                disk_pct = primary['usage_percent']
                disk_status = "ok" if disk_pct < 80 else ("warning" if disk_pct < 95 else "error")
                self._disk_card.set_value(f"{disk_pct:.1f}", disk_status)

                # Clear and rebuild disk list
                self._clear_layout(self._disk_container)
                for disk in disks:
                    disk_frame = QFrame()
                    disk_frame.setObjectName("card")
                    dl = QVBoxLayout(disk_frame)
                    dl.addWidget(InfoRow("Device", disk['device']))
                    dl.addWidget(InfoRow("Mount", disk['mountpoint']))
                    dl.addWidget(InfoRow("Filesystem", disk['filesystem']))
                    dl.addWidget(InfoRow("Total", system_info.format_bytes(disk['total_bytes'])))
                    dl.addWidget(InfoRow("Used", f"{system_info.format_bytes(disk['used_bytes'])} ({disk['usage_percent']:.1f}%)"))
                    dl.addWidget(InfoRow("Free", system_info.format_bytes(disk['free_bytes'])))
                    self._disk_container.addWidget(disk_frame)

            # Network
            interfaces = system_info.get_network_interfaces()
            self._clear_layout(self._network_container)
            for iface in interfaces:
                if not iface['is_up'] and iface['name'] != "lo":
                    continue  # Skip down interfaces except loopback
                net_frame = QFrame()
                net_frame.setObjectName("card")
                nl = QVBoxLayout(net_frame)
                status_str = "● Up" if iface['is_up'] else "○ Down"
                nl.addWidget(InfoRow("Interface", f"{iface['name']}  {status_str}"))
                if iface['ipv4']:
                    nl.addWidget(InfoRow("IPv4", iface['ipv4']))
                if iface['mac']:
                    nl.addWidget(InfoRow("MAC", iface['mac']))
                if iface['speed_mbps']:
                    nl.addWidget(InfoRow("Speed", f"{iface['speed_mbps']} Mbps"))
                nl.addWidget(InfoRow("Traffic",
                    f"↑ {system_info.format_bytes(iface['bytes_sent'])}  "
                    f"↓ {system_info.format_bytes(iface['bytes_recv'])}"
                ))
                self._network_container.addWidget(net_frame)

        except Exception as e:
            # If we can't get data, show the error — never fake it
            self._hostname_label.setText(f"Error: {e}")

    def _clear_layout(self, layout):
        """Remove all widgets from a layout."""
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
