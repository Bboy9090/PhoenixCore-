import sys
import os
import json
import random
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QMessageBox
from PyQt6.QtGui import QPainter, QColor, QFont, QKeyEvent, QLinearGradient
from PyQt6.QtCore import Qt, QTimer, QRectF

SAVE_DIR = Path.home() / ".soul_journey"
SAVE_FILE = SAVE_DIR / "highscore.json"

class GameCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMinimumSize(800, 800)
        
        # Game Constants
        self.FPS = 60
        self.STRIKE_ZONE_Y = 650
        self.STRIKE_ZONE_H = 60
        self.NOTE_SPEED = 8.0 # Pixels per frame
        self.TRACK_WIDTH = 100
        self.TRACK_X_START = 200 # Centering the 4 tracks (400px total width)
        
        # Game State
        self.is_playing = False
        self.score = 0
        self.high_score = self.load_high_score()
        self.combo = 0
        self.multiplier = 1
        self.notes = [] # List of dicts: {'track': int (0-3), 'y': float}
        self.feedback = "" # Perfect, Good, Miss
        self.feedback_timer = 0
        
        # Timers
        self.game_timer = QTimer(self)
        self.game_timer.timeout.connect(self.game_loop)
        
        self.spawn_timer = QTimer(self)
        self.spawn_timer.timeout.connect(self.spawn_note)
        
        # Start Screen
        self.show_start_screen = True

    def load_high_score(self):
        try:
            os.makedirs(SAVE_DIR, exist_ok=True)
            if SAVE_FILE.exists():
                with open(SAVE_FILE, "r") as f:
                    data = json.load(f)
                    return data.get("high_score", 0)
        except:
            pass
        return 0

    def save_high_score(self):
        try:
            with open(SAVE_FILE, "w") as f:
                json.dump({"high_score": self.high_score}, f)
        except Exception as e:
            print(f"Failed to save high score: {e}")

    def start_game(self):
        self.show_start_screen = False
        self.is_playing = True
        self.score = 0
        self.combo = 0
        self.multiplier = 1
        self.notes.clear()
        self.feedback = ""
        
        self.game_timer.start(1000 // self.FPS)
        self.spawn_timer.start(600) # Spawn a note every 600ms

    def end_game(self):
        self.is_playing = False
        self.game_timer.stop()
        self.spawn_timer.stop()
        if self.score > self.high_score:
            self.high_score = self.score
            self.save_high_score()
        self.show_start_screen = True
        self.update()

    def spawn_note(self):
        track = random.randint(0, 3)
        self.notes.append({'track': track, 'y': -50.0})
        
        # Slowly increase difficulty (decrease spawn time)
        current_interval = self.spawn_timer.interval()
        if current_interval > 250:
            self.spawn_timer.setInterval(current_interval - 5)

    def game_loop(self):
        # Move notes
        for note in self.notes:
            note['y'] += self.NOTE_SPEED
            
        # Check for missed notes
        missed = [n for n in self.notes if n['y'] > self.height()]
        for m in missed:
            self.register_hit("MISS", 0)
            self.notes.remove(m)
            
        # Update feedback timer
        if self.feedback_timer > 0:
            self.feedback_timer -= 1
            
        self.update() # Trigger paintEvent

    def keyPressEvent(self, event: QKeyEvent):
        if self.show_start_screen:
            if event.key() == Qt.Key.Key_Space:
                self.start_game()
            return

        if not self.is_playing: return

        # Map keys to tracks 0, 1, 2, 3
        key_map = {
            Qt.Key.Key_A: 0,
            Qt.Key.Key_S: 1,
            Qt.Key.Key_D: 2,
            Qt.Key.Key_F: 3
        }
        
        if event.key() == Qt.Key.Key_Escape:
            self.end_game()
            return

        track = key_map.get(event.key())
        if track is not None:
            self.handle_hit(track)

    def handle_hit(self, track):
        # Find the lowest note in this track
        track_notes = [n for n in self.notes if n['track'] == track]
        if not track_notes:
            return # No note to hit
            
        lowest_note = max(track_notes, key=lambda n: n['y'])
        
        # Calculate distance to center of strike zone
        target_y = self.STRIKE_ZONE_Y + (self.STRIKE_ZONE_H / 2)
        note_y = lowest_note['y'] + 15 # center of note roughly
        distance = abs(target_y - note_y)
        
        if distance < 30:
            self.register_hit("PERFECT", 100)
            self.notes.remove(lowest_note)
        elif distance < 70:
            self.register_hit("GOOD", 50)
            self.notes.remove(lowest_note)
        elif distance < 120:
            self.register_hit("MISS", 0)
            # Remove it so we don't double punish, but break combo
            self.notes.remove(lowest_note)

    def register_hit(self, quality, base_points):
        self.feedback = quality
        self.feedback_timer = 30 # Show feedback for 30 frames
        
        if quality == "MISS":
            self.combo = 0
            self.multiplier = 1
            # Optional: end game on too many misses, but we'll let it play endlessly for now
        else:
            self.combo += 1
            self.multiplier = min(4, 1 + (self.combo // 10))
            self.score += base_points * self.multiplier

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor("#050811"))
        
        # Tracks Background
        painter.fillRect(self.TRACK_X_START, 0, self.TRACK_WIDTH * 4, self.height(), QColor(255, 255, 255, 10))
        
        # Track Separators
        painter.setPen(QColor(255, 255, 255, 30))
        for i in range(5):
            x = self.TRACK_X_START + (i * self.TRACK_WIDTH)
            painter.drawLine(x, 0, x, self.height())
            
        # Strike Zone
        sz_color = QColor(0, 200, 200, 50) # Glowing Teal
        painter.fillRect(self.TRACK_X_START, self.STRIKE_ZONE_Y, self.TRACK_WIDTH * 4, self.STRIKE_ZONE_H, sz_color)
        
        # Track Labels (A, S, D, F)
        painter.setPen(QColor(255, 255, 255, 150))
        painter.setFont(QFont("Inter", 24, QFont.Weight.Bold))
        labels = ["A", "S", "D", "F"]
        for i, label in enumerate(labels):
            x = self.TRACK_X_START + (i * self.TRACK_WIDTH) + 35
            painter.drawText(x, self.STRIKE_ZONE_Y + 40, label)

        if self.show_start_screen:
            self.draw_start_screen(painter)
            return

        # Draw Notes
        note_colors = [
            QColor(255, 50, 50),   # Red
            QColor(255, 215, 0),   # Gold
            QColor(0, 200, 200),   # Teal
            QColor(150, 80, 255)   # Violet
        ]
        
        for note in self.notes:
            color = note_colors[note['track']]
            x = self.TRACK_X_START + (note['track'] * self.TRACK_WIDTH) + 20
            
            # Glowing note effect
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(int(x), int(note['y']), 60, 30, 15, 15)
            
            # Inner white core
            painter.setBrush(QColor(255, 255, 255, 200))
            painter.drawRoundedRect(int(x) + 15, int(note['y']) + 5, 30, 20, 10, 10)

        # Draw HUD (Score, Combo)
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Inter", 20, QFont.Weight.Bold))
        painter.drawText(20, 40, f"SCORE: {self.score}")
        painter.drawText(20, 80, f"HIGH: {self.high_score}")
        
        if self.combo > 5:
            painter.setPen(QColor(255, 215, 0)) # Gold for high combo
            painter.drawText(20, 120, f"COMBO: {self.combo}x")
            painter.drawText(20, 160, f"MULT: {self.multiplier}x")

        # Draw Feedback Text (Perfect, Good, Miss)
        if self.feedback_timer > 0:
            if self.feedback == "PERFECT":
                painter.setPen(QColor(0, 255, 255)) # Cyan
            elif self.feedback == "GOOD":
                painter.setPen(QColor(255, 255, 0)) # Yellow
            else:
                painter.setPen(QColor(255, 0, 0)) # Red
                
            painter.setFont(QFont("Inter", 48, QFont.Weight.Black))
            painter.drawText(self.TRACK_X_START + 80, self.STRIKE_ZONE_Y - 50, self.feedback)

    def draw_start_screen(self, painter):
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Inter", 48, QFont.Weight.Black))
        painter.drawText(self.width() // 2 - 200, self.height() // 2 - 50, "SOUL JOURNEY")
        
        painter.setFont(QFont("Inter", 20))
        painter.setPen(QColor(200, 200, 200))
        painter.drawText(self.width() // 2 - 220, self.height() // 2 + 20, "Press [SPACE] to start the rhythm")
        
        painter.drawText(self.width() // 2 - 250, self.height() // 2 + 80, "Use A, S, D, F as notes hit the Strike Zone")
        
        painter.setFont(QFont("Inter", 24, QFont.Weight.Bold))
        painter.setPen(QColor(255, 215, 0))
        painter.drawText(self.width() // 2 - 120, self.height() // 2 + 150, f"HIGH SCORE: {self.high_score}")

class SoulJourneyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Soul Journey - Phoenix OS Flagship")
        self.setFixedSize(800, 800)
        
        self.canvas = GameCanvas(self)
        self.setCentralWidget(self.canvas)
        
    def closeEvent(self, event):
        # Ensure high score is saved if closed mid-game
        if self.canvas.is_playing:
            self.canvas.end_game()
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = SoulJourneyApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
