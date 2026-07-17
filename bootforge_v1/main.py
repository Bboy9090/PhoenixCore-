from __future__ import annotations

import logging
import sys
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from bootforge_v1.services.usb_service import UsbService


def configure_logging() -> Path:
    log_dir = Path.home() / "BootForge" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "bootforge-v1.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[logging.FileHandler(log_path, encoding="utf-8"), logging.StreamHandler()],
    )
    return log_path


class BootForgeWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.usb_service = UsbService()
        self.setWindowTitle("BootForge aka USB Creator v1")
        self.resize(980, 680)

        container = QWidget(self)
        layout = QVBoxLayout(container)

        title = QLabel("BootForge aka USB Creator v1")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: 700; padding: 12px;")

        self.security_label = QLabel("Secure registry: not checked")
        self.security_label.setAlignment(Qt.AlignCenter)

        self.device_list = QListWidget()
        self.refresh_button = QPushButton("Scan removable devices safely")
        self.refresh_button.clicked.connect(self.refresh_devices)

        layout.addWidget(title)
        layout.addWidget(self.security_label)
        layout.addWidget(self.refresh_button)
        layout.addWidget(self.device_list)

        self.setCentralWidget(container)
        self.setStatusBar(QStatusBar(self))
        self.statusBar().showMessage("Dry-run safety mode active. No disk writes are enabled.")
        self.refresh_devices()

    def refresh_devices(self) -> None:
        self.device_list.clear()
        try:
            status = self.usb_service.dry_run_status()
            secure = bool(status["secure_registry"])
            self.security_label.setText(
                "Secure registry: VERIFIED" if secure else "Secure registry: UNAVAILABLE"
            )
            devices = status["devices"]
            if not devices:
                self.device_list.addItem("No removable devices detected.")
            for device in devices:
                gib = device.total_bytes / (1024 ** 3) if device.total_bytes else 0
                self.device_list.addItem(f"{device.path} | {device.label} | {gib:.2f} GiB")
            self.statusBar().showMessage(
                f"Scan complete. {len(devices)} removable device(s). Dry-run mode remains active."
            )
        except SystemExit:
            QMessageBox.critical(
                self,
                "BootForge Security Halt",
                "The signed tool registry failed validation. BootForge blocked startup work.",
            )
            self.security_label.setText("Secure registry: FAILED")
        except Exception as exc:
            logging.getLogger(__name__).exception("Device scan failed")
            QMessageBox.critical(self, "BootForge Error", str(exc))


def main() -> int:
    log_path = configure_logging()
    logging.getLogger(__name__).info("BootForge v1 starting; log=%s", log_path)
    app = QApplication(sys.argv)
    window = BootForgeWindow()
    window.show()
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
