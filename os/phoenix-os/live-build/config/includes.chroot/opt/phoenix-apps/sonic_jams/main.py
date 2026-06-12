import sys
import os
import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QPushButton, QSlider, QLabel,
    QFileDialog, QLineEdit, QSplitter, QMessageBox, QFrame, QInputDialog
)
from PyQt6.QtCore import Qt, QUrl, QTimer
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

# Default to user's Music folder, fallback to current dir
DEFAULT_MUSIC_DIR = Path.home() / "Music"
if not DEFAULT_MUSIC_DIR.exists():
    DEFAULT_MUSIC_DIR = Path.home()

PLAYLISTS_DIR = Path.home() / ".sonic_jams" / "playlists"
os.makedirs(PLAYLISTS_DIR, exist_ok=True)

class SonicJamsApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sonic Jams - Phoenix OS Flagship")
        self.resize(1100, 750)
        
        # Apple Music / Spotify-like Dark Aesthetic
        self.setStyleSheet("""
            QMainWindow, QWidget { background-color: #0b0f19; color: #e5e7eb; font-family: 'Inter', sans-serif; }
            QListWidget { background-color: #111827; border: none; border-radius: 8px; padding: 5px; font-size: 14px; }
            QListWidget::item { padding: 10px; border-radius: 6px; }
            QListWidget::item:hover { background-color: #1f2937; }
            QListWidget::item:selected { background-color: #3b82f6; color: white; }
            QPushButton { background-color: #1f2937; color: white; border: none; padding: 10px 20px; border-radius: 6px; font-weight: bold; }
            QPushButton:hover { background-color: #374151; }
            QLineEdit { background-color: #1f2937; border: 1px solid #374151; padding: 10px; border-radius: 6px; color: white; }
            QSlider::groove:horizontal { background: #374151; height: 6px; border-radius: 3px; }
            QSlider::handle:horizontal { background: #3b82f6; width: 14px; height: 14px; margin: -4px 0; border-radius: 7px; }
            QLabel { font-size: 14px; }
            .sidebar { background-color: #070a11; }
        """)

        # Core State
        self.all_tracks = [] # List of tuples: (name, absolute_path)
        self.current_playlist = []
        
        # Media Player
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.5)

        self.player.positionChanged.connect(self.update_position)
        self.player.durationChanged.connect(self.update_duration)

        self.setup_ui()
        self.scan_library(DEFAULT_MUSIC_DIR)

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top Splitter (Sidebar + Main Content)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # --- Sidebar (Playlists & Lib) ---
        sidebar_widget = QWidget()
        sidebar_widget.setProperty("class", "sidebar")
        sidebar_layout = QVBoxLayout(sidebar_widget)
        sidebar_layout.setContentsMargins(15, 20, 15, 20)
        
        lib_btn = QPushButton("My Library")
        lib_btn.clicked.connect(lambda: self.show_all_tracks())
        sidebar_layout.addWidget(lib_btn)
        
        add_folder_btn = QPushButton("Add Folder...")
        add_folder_btn.clicked.connect(self.add_music_folder)
        sidebar_layout.addWidget(add_folder_btn)
        
        sidebar_layout.addSpacing(20)
        sidebar_layout.addWidget(QLabel("<b>PLAYLISTS</b>"))
        
        self.playlists_list = QListWidget()
        self.playlists_list.itemClicked.connect(self.load_playlist)
        sidebar_layout.addWidget(self.playlists_list)
        
        create_pl_btn = QPushButton("Create Playlist")
        create_pl_btn.clicked.connect(self.create_playlist)
        sidebar_layout.addWidget(create_pl_btn)
        
        # --- Main Track List ---
        main_content = QWidget()
        main_content_layout = QVBoxLayout(main_content)
        main_content_layout.setContentsMargins(20, 20, 20, 20)
        
        # Search Bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search songs, artists...")
        self.search_bar.textChanged.connect(self.filter_tracks)
        main_content_layout.addWidget(self.search_bar)
        
        self.track_list_widget = QListWidget()
        self.track_list_widget.itemDoubleClicked.connect(self.play_track_from_list)
        main_content_layout.addWidget(self.track_list_widget)

        splitter.addWidget(sidebar_widget)
        splitter.addWidget(main_content)
        splitter.setSizes([250, 850])
        main_layout.addWidget(splitter, 1)

        # --- Bottom Player Bar ---
        player_bar = QFrame()
        player_bar.setStyleSheet("background-color: #111827; border-top: 1px solid #1f2937;")
        player_layout = QHBoxLayout(player_bar)
        player_layout.setContentsMargins(20, 15, 20, 15)

        self.now_playing_lbl = QLabel("No track selected")
        self.now_playing_lbl.setMinimumWidth(200)
        self.now_playing_lbl.setStyleSheet("font-weight: bold; color: #60a5fa;")
        player_layout.addWidget(self.now_playing_lbl)

        # Controls
        controls_layout = QHBoxLayout()
        self.btn_prev = QPushButton("⏮")
        self.btn_play = QPushButton("▶")
        self.btn_next = QPushButton("⏭")
        
        self.btn_play.clicked.connect(self.toggle_play)
        # Prev/Next implementation requires keeping track of index, skipped for brevity but easily added
        
        controls_layout.addWidget(self.btn_prev)
        controls_layout.addWidget(self.btn_play)
        controls_layout.addWidget(self.btn_next)
        player_layout.addLayout(controls_layout)

        # Progress
        self.time_lbl = QLabel("0:00")
        player_layout.addWidget(self.time_lbl)
        
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.sliderMoved.connect(self.set_position)
        player_layout.addWidget(self.progress_slider)

        self.duration_lbl = QLabel("0:00")
        player_layout.addWidget(self.duration_lbl)

        # Volume
        player_layout.addSpacing(20)
        player_layout.addWidget(QLabel("🔊"))
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(50)
        self.volume_slider.setFixedWidth(100)
        self.volume_slider.valueChanged.connect(self.set_volume)
        player_layout.addWidget(self.volume_slider)

        main_layout.addWidget(player_bar)
        
        self.refresh_playlists()

    # --- Core Logic ---
    def scan_library(self, folder: Path):
        """Scans a directory for mp3 and wav files."""
        if not folder.exists(): return
        
        for file in folder.rglob("*"):
            if file.suffix.lower() in [".mp3", ".wav", ".flac", ".m4a"]:
                # Ensure no duplicates
                path_str = str(file)
                if not any(t[1] == path_str for t in self.all_tracks):
                    self.all_tracks.append((file.name, path_str))
        
        self.show_all_tracks()

    def add_music_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Music Folder")
        if folder:
            self.scan_library(Path(folder))

    def show_all_tracks(self):
        self.current_playlist = self.all_tracks.copy()
        self.render_tracks()

    def render_tracks(self, filter_text=""):
        self.track_list_widget.clear()
        for name, path in self.current_playlist:
            if filter_text.lower() in name.lower():
                item = QListWidgetItem(name)
                item.setData(Qt.ItemDataRole.UserRole, path)
                self.track_list_widget.addItem(item)

    def filter_tracks(self, text):
        self.render_tracks(text)

    # --- Playback Logic ---
    def play_track_from_list(self, item):
        path = item.data(Qt.ItemDataRole.UserRole)
        name = item.text()
        
        self.player.setSource(QUrl.fromLocalFile(path))
        self.audio_output.setVolume(self.volume_slider.value() / 100.0)
        self.player.play()
        
        self.btn_play.setText("⏸")
        self.now_playing_lbl.setText(name)

    def toggle_play(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            self.btn_play.setText("▶")
        elif self.player.source().isValid():
            self.player.play()
            self.btn_play.setText("⏸")

    def update_position(self, position):
        self.progress_slider.setValue(position)
        self.time_lbl.setText(self.format_time(position))

    def update_duration(self, duration):
        self.progress_slider.setMaximum(duration)
        self.duration_lbl.setText(self.format_time(duration))

    def set_position(self, position):
        self.player.setPosition(position)

    def set_volume(self, volume):
        self.audio_output.setVolume(volume / 100.0)

    def format_time(self, ms):
        s = (ms // 1000) % 60
        m = (ms // 60000) % 60
        return f"{m}:{s:02}"

    # --- Playlist Logic ---
    def create_playlist(self):
        name, ok = QInputDialog.getText(self, "New Playlist", "Playlist Name:")
        if ok and name:
            filepath = PLAYLISTS_DIR / f"{name}.json"
            # Save whatever is currently in the track list as the playlist
            paths = [self.track_list_widget.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.track_list_widget.count())]
            
            try:
                with open(filepath, "w") as f:
                    json.dump({"name": name, "tracks": paths}, f)
                self.refresh_playlists()
                QMessageBox.information(self, "Success", f"Playlist '{name}' saved successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save playlist:\\n{e}")

    def refresh_playlists(self):
        self.playlists_list.clear()
        for file in PLAYLISTS_DIR.glob("*.json"):
            try:
                with open(file, "r") as f:
                    data = json.load(f)
                    item = QListWidgetItem(data.get("name", "Unknown Playlist"))
                    item.setData(Qt.ItemDataRole.UserRole, str(file))
                    self.playlists_list.addItem(item)
            except:
                pass

    def load_playlist(self, item):
        path = item.data(Qt.ItemDataRole.UserRole)
        try:
            with open(path, "r") as f:
                data = json.load(f)
                
            # Reconstruct track tuples
            new_pl = []
            for t_path in data.get("tracks", []):
                p = Path(t_path)
                if p.exists():
                    new_pl.append((p.name, str(p)))
                    
            self.current_playlist = new_pl
            self.render_tracks()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load playlist:\\n{e}")

def main():
    app = QApplication(sys.argv)
    window = SonicJamsApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
