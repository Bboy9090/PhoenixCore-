"""
Device Inspector — Real hardware device enumeration.
USB, PCI, Network Adapters, Storage Devices — all from real system tools.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QScrollArea, QTabWidget,
)
from PyQt6.QtCore import QTimer

from arcwyre.services import hardware_info, system_info
from arcwyre.widgets.status_card import SectionHeader, InfoRow, NotImplementedLabel
from arcwyre.widgets.data_table import DataTable
from arcwyre.theme import COLORS


class InspectorModule(QWidget):
    """Device Inspector — lists all detected hardware from real sources."""

    MODULE_ID = "inspector"
    MODULE_TITLE = "Device Inspector"
    MODULE_SUBTITLE = "Hardware Detection & Enumeration"
    MODULE_ICON = "🔍"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        tabs = QTabWidget()

        # ── USB Devices ────────────────────────────────────────────────
        usb_tab = QWidget()
        usb_layout = QVBoxLayout(usb_tab)
        self._usb_table = DataTable(["Bus", "ID", "Device Name"])
        usb_layout.addWidget(self._usb_table)
        tabs.addTab(usb_tab, "🔌  USB Devices")

        # ── PCI Devices ────────────────────────────────────────────────
        pci_tab = QWidget()
        pci_layout = QVBoxLayout(pci_tab)
        self._pci_table = DataTable(["Slot", "Class", "Device", "Vendor"])
        pci_layout.addWidget(self._pci_table)
        tabs.addTab(pci_tab, "🔧  PCI Devices")

        # ── CPU Architecture ───────────────────────────────────────────
        cpu_tab = QWidget()
        cpu_layout = QVBoxLayout(cpu_tab)
        self._cpu_container = QVBoxLayout()
        cpu_layout.addLayout(self._cpu_container)
        cpu_layout.addStretch()
        tabs.addTab(cpu_tab, "🧠  CPU")

        # ── Memory SPD ─────────────────────────────────────────────────
        mem_tab = QWidget()
        mem_layout = QVBoxLayout(mem_tab)
        self._mem_container = QVBoxLayout()
        mem_layout.addLayout(self._mem_container)
        mem_layout.addStretch()
        tabs.addTab(mem_tab, "🖨️  Memory")

        # ── Network Adapters ───────────────────────────────────────────
        net_tab = QWidget()
        net_layout = QVBoxLayout(net_tab)
        self._net_table = DataTable(["Interface", "IPv4", "MAC", "Status", "Speed"])
        net_layout.addWidget(self._net_table)
        tabs.addTab(net_tab, "🌐  Network")

        # ── Storage Devices ────────────────────────────────────────────
        storage_tab = QWidget()
        storage_layout = QVBoxLayout(storage_tab)
        self._storage_table = DataTable(["Device", "Mount", "Filesystem", "Size", "Used", "Free"])
        storage_layout.addWidget(self._storage_table)
        tabs.addTab(storage_tab, "💾  Storage")

        # ── GPU ────────────────────────────────────────────────────────
        gpu_tab = QWidget()
        gpu_layout = QVBoxLayout(gpu_tab)
        self._gpu_container = QVBoxLayout()
        gpu_layout.addLayout(self._gpu_container)
        gpu_layout.addStretch()
        tabs.addTab(gpu_tab, "🎮  GPU")

        # ── System Info ────────────────────────────────────────────────
        sys_tab = QWidget()
        sys_layout = QVBoxLayout(sys_tab)
        self._sys_container = QVBoxLayout()
        sys_layout.addLayout(self._sys_container)
        sys_layout.addStretch()
        tabs.addTab(sys_tab, "ℹ️  System")

        layout.addWidget(tabs)

        # Refresh button
        from PyQt6.QtWidgets import QPushButton
        refresh_btn = QPushButton("🔄  Refresh All Devices")
        refresh_btn.setObjectName("primary_button")
        refresh_btn.clicked.connect(self._load_data)
        layout.addWidget(refresh_btn)

        scroll.setWidget(content)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def _load_data(self):
        """Load all device data from real system sources."""
        self._load_cpu()
        self._load_memory()
        self._load_usb()
        self._load_pci()
        self._load_network()
        self._load_storage()
        self._load_gpu()
        self._load_system_info()

    def _load_cpu(self):
        self._clear_layout(self._cpu_container)
        self._cpu_container.addWidget(SectionHeader("Processor Architecture"))
        
        cpu_frame = QFrame()
        cpu_frame.setObjectName("card")
        cl = QVBoxLayout(cpu_frame)
        
        # We will extract real lscpu/sysctl data.
        import subprocess
        import platform
        
        system = platform.system()
        if system == "Linux":
            try:
                out = subprocess.check_output("lscpu", shell=True, text=True)
                lines = out.split("\n")
                for line in lines:
                    if ":" in line:
                        k, v = line.split(":", 1)
                        if k.strip() in ["Model name", "Architecture", "CPU(s)", "Thread(s) per core", "Core(s) per socket", "Socket(s)", "L1d cache", "L1i cache", "L2 cache", "L3 cache"]:
                            cl.addWidget(InfoRow(k.strip(), v.strip()))
            except Exception as e:
                cl.addWidget(NotImplementedLabel(f"Error parsing lscpu: {e}"))
        elif system == "Darwin":
            try:
                out = subprocess.check_output("sysctl -a | grep machdep.cpu", shell=True, text=True)
                for line in out.split("\n"):
                    if "brand_string" in line:
                        cl.addWidget(InfoRow("Model Name", line.split(":")[1].strip()))
                    elif "core_count" in line:
                        cl.addWidget(InfoRow("Cores", line.split(":")[1].strip()))
                    elif "thread_count" in line:
                        cl.addWidget(InfoRow("Threads", line.split(":")[1].strip()))
            except Exception as e:
                cl.addWidget(NotImplementedLabel(f"Error parsing sysctl: {e}"))
        else:
            cl.addWidget(NotImplementedLabel("CPU detail parsing not supported on this OS"))
            
        self._cpu_container.addWidget(cpu_frame)

    def _load_memory(self):
        self._clear_layout(self._mem_container)
        self._mem_container.addWidget(SectionHeader("Memory SPD & Timings"))
        
        mem_frame = QFrame()
        mem_frame.setObjectName("card")
        ml = QVBoxLayout(mem_frame)
        
        import platform
        if platform.system() == "Linux":
            ml.addWidget(NotImplementedLabel("Requires root access. Run: sudo dmidecode -t memory"))
        elif platform.system() == "Darwin":
            try:
                import subprocess
                out = subprocess.check_output("system_profiler SPMemoryDataType", shell=True, text=True)
                for line in out.split("\n"):
                    if "Size:" in line or "Type:" in line or "Speed:" in line or "Manufacturer:" in line:
                        k, v = line.split(":", 1)
                        ml.addWidget(InfoRow(k.strip(), v.strip()))
            except:
                ml.addWidget(NotImplementedLabel("Failed to read Memory SPD"))
        else:
            ml.addWidget(NotImplementedLabel("Memory SPD parsing not supported on this OS"))
            
        self._mem_container.addWidget(mem_frame)

    def _load_usb(self):
        devices = hardware_info.get_usb_devices()
        rows = []
        for d in devices:
            if "error" in d:
                self._usb_table.set_data([[d["error"], "", ""]])
                return
            rows.append([
                d.get("bus", ""),
                d.get("id", ""),
                d.get("name", d.get("product name", "Unknown")),
            ])
        self._usb_table.set_data(rows if rows else [["No USB devices detected", "", ""]])

    def _load_pci(self):
        devices = hardware_info.get_pci_devices()
        rows = []
        for d in devices:
            if "error" in d:
                self._pci_table.set_data([[d["error"], "", "", ""]])
                return
            rows.append([
                d.get("slot", d.get("name", "")),
                d.get("class", d.get("type", "")),
                d.get("device", d.get("name", "")),
                d.get("vendor", ""),
            ])
        self._pci_table.set_data(rows if rows else [["No PCI devices detected", "", "", ""]])

    def _load_network(self):
        interfaces = system_info.get_network_interfaces()
        rows = []
        for iface in interfaces:
            rows.append([
                iface["name"],
                iface["ipv4"] or "—",
                iface["mac"] or "—",
                "Up" if iface["is_up"] else "Down",
                f"{iface['speed_mbps']} Mbps" if iface['speed_mbps'] else "—",
            ])
        self._net_table.set_data(rows)

    def _load_storage(self):
        disks = system_info.get_disk_info()
        rows = []
        for d in disks:
            rows.append([
                d["device"],
                d["mountpoint"],
                d["filesystem"],
                system_info.format_bytes(d["total_bytes"]),
                system_info.format_bytes(d["used_bytes"]),
                system_info.format_bytes(d["free_bytes"]),
            ])
        self._storage_table.set_data(rows)

    def _load_gpu(self):
        self._clear_layout(self._gpu_container)
        gpus = hardware_info.get_gpu_info()
        if not gpus or (len(gpus) == 1 and "error" in gpus[0]):
            error_msg = gpus[0].get("error", "No GPU detected") if gpus else "No GPU detected"
            self._gpu_container.addWidget(NotImplementedLabel(error_msg))
            return

        for gpu in gpus:
            gpu_frame = QFrame()
            gpu_frame.setObjectName("card")
            gl = QVBoxLayout(gpu_frame)
            for key, value in gpu.items():
                gl.addWidget(InfoRow(key.replace("_", " ").title(), str(value)))
            self._gpu_container.addWidget(gpu_frame)

    def _load_system_info(self):
        self._clear_layout(self._sys_container)
        os_info = system_info.get_os_info()
        bios = hardware_info.get_bios_info()

        # OS Info
        self._sys_container.addWidget(SectionHeader("Operating System"))
        os_frame = QFrame()
        os_frame.setObjectName("card")
        ol = QVBoxLayout(os_frame)
        ol.addWidget(InfoRow("System", os_info["system"]))
        ol.addWidget(InfoRow("Release", os_info["release"]))
        ol.addWidget(InfoRow("Version", os_info["version"]))
        ol.addWidget(InfoRow("Architecture", os_info["machine"]))
        ol.addWidget(InfoRow("Processor", os_info["processor"]))
        ol.addWidget(InfoRow("Hostname", system_info.get_hostname()))
        ol.addWidget(InfoRow("Uptime", system_info.format_uptime(system_info.get_uptime_seconds())))
        self._sys_container.addWidget(os_frame)

        # BIOS/Firmware
        self._sys_container.addWidget(SectionHeader("BIOS / Firmware"))
        bios_frame = QFrame()
        bios_frame.setObjectName("card")
        bl = QVBoxLayout(bios_frame)
        if "error" in bios:
            bl.addWidget(NotImplementedLabel(bios["error"]))
        else:
            for key, value in bios.items():
                bl.addWidget(InfoRow(key.replace("_", " ").title(), str(value)))
        self._sys_container.addWidget(bios_frame)

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
