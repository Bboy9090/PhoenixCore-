"""
Chrome OS recovery download UI for BootForge USB Recipe Manager.

Uses chromeos-releases-data index (CC-BY) and dl.google.com recovery URLs.
See docs/CHROMEOS_RECOVERY.md.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QObject, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.core.chromeos_recovery import (
    RecoverySelection,
    DEFAULT_INDEX_URL,
    download_recovery_zip,
    fetch_index,
    select_recovery_for_board,
)


class ChromeosDownloadWorker(QObject):
    finished = pyqtSignal(object, object, object)  # sel|None, path|None, err|None
    progress = pyqtSignal(int, object)  # done bytes, total Optional[int]

    def __init__(self, board: str, dest_path: Path, index_url: Optional[str] = None):
        super().__init__()
        self.board = board.strip()
        self.dest_path = dest_path
        self.index_url = index_url or DEFAULT_INDEX_URL

    def run(self) -> None:
        try:
            index = fetch_index(self.index_url)
            sel = select_recovery_for_board(index, self.board)

            def _cb(done: int, total: Optional[int]) -> None:
                self.progress.emit(done, total)

            download_recovery_zip(sel.url, self.dest_path, progress_callback=_cb)
            self.finished.emit(sel, str(self.dest_path.resolve()), None)
        except Exception as e:
            self.finished.emit(None, None, e)


class ChromeosRecoveryWidget(QWidget):
    """
    Board input + download button. On success, exposes last_zip_path and emits chromeos_download_finished(path, board).
    """

    chromeos_download_finished = pyqtSignal(str, str)  # path, board

    def __init__(self, cache_dir: Optional[Path] = None):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self._thread: Optional[QThread] = None
        self._worker: Optional[ChromeosDownloadWorker] = None
        self.last_zip_path: Optional[str] = None
        self.last_board: Optional[str] = None

        base = cache_dir or (Path.home() / ".bootforge" / "chromeos_recovery")
        self.cache_dir = Path(base)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        layout = QVBoxLayout(self)
        intro = QLabel(
            "Enter your Chromebook <b>board</b> codename (e.g. octopus, hatch, brya). "
            "Wrong board can fail recovery. Metadata: chromeos-releases-data (CC-BY); files from Google."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        row = QHBoxLayout()
        row.addWidget(QLabel("Board:"))
        self.board_edit = QLineEdit()
        self.board_edit.setPlaceholderText("e.g. octopus")
        row.addWidget(self.board_edit)
        layout.addLayout(row)

        self.download_btn = QPushButton("Download recovery ZIP")
        self.download_btn.clicked.connect(self._on_download)
        layout.addWidget(self.download_btn)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(120)
        layout.addWidget(self.log)

        hint = QLabel('Docs: <a href="https://github.com/MercuryWorkshop/chromeos-releases-data">chromeos-releases-data</a>')
        hint.setOpenExternalLinks(True)
        layout.addWidget(hint)

    def reset_for_new_recipe(self) -> None:
        self.last_zip_path = None
        self.last_board = None
        self.log.clear()
        self.progress.setVisible(False)

    def _on_download(self) -> None:
        board = self.board_edit.text().strip()
        if not board:
            QMessageBox.warning(self, "Board required", "Enter a Chrome OS board codename.")
            return

        safe = board.lower().replace("/", "_")
        dest = self.cache_dir / f"chromeos_{safe}_recovery.zip"

        self.download_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.log.append(f"Fetching index and downloading to:\n{dest}")

        self._thread = QThread()
        self._worker = ChromeosDownloadWorker(board, dest, None)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._thread.start()

    def _on_progress(self, done: int, total: object) -> None:
        if total is not None and isinstance(total, int) and total > 0:
            self.progress.setRange(0, 100)
            self.progress.setValue(int(100 * done / total))
        else:
            self.progress.setRange(0, 0)

    def _on_finished(self, sel: object, saved_path: object, err: object) -> None:
        self.download_btn.setEnabled(True)
        self.progress.setVisible(False)
        if self._thread:
            self._thread.quit()
            self._thread.wait(3000)
        self._thread = None
        self._worker = None

        if err is not None:
            self.log.append(f"Error: {err}")
            QMessageBox.critical(self, "Download failed", str(err))
            return

        if not isinstance(sel, RecoverySelection) or not isinstance(saved_path, str):
            return

        self.last_zip_path = saved_path
        self.last_board = sel.board
        self.log.append(
            f"OK: {sel.platform_version} chrome={sel.chrome_version}\nSaved: {self.last_zip_path}"
        )
        self.chromeos_download_finished.emit(self.last_zip_path, sel.board)
        QMessageBox.information(
            self,
            "Download complete",
            f"Recovery ZIP saved.\n\n{self.last_zip_path}\n\n"
            "Optional: in USB Deployment Builder, tab 5, enable flash to USB and confirm warnings "
            "to write from BootForge. Or unzip the .bin and use Chromebook Recovery Utility or another verified tool.",
        )
