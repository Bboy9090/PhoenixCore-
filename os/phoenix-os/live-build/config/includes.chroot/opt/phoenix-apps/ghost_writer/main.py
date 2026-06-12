import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QFileDialog, 
    QMessageBox, QToolBar
)
from PyQt6.QtGui import QAction, QIcon, QFont
from PyQt6.QtCore import Qt

class GhostWriterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ghost Writer - Phoenix OS")
        self.resize(1000, 700)
        
        # Apply a flawless, clean dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0b0f19;
            }
            QTextEdit {
                background-color: #111827;
                color: #e5e7eb;
                border: none;
                padding: 20px;
                font-size: 16px;
                font-family: 'Inter', 'Segoe UI', sans-serif;
                selection-background-color: #3b82f6;
            }
            QToolBar {
                background-color: #1f2937;
                border: none;
                padding: 5px;
            }
            QToolBar QToolButton {
                color: #d1d5db;
                padding: 6px;
                border-radius: 4px;
            }
            QToolBar QToolButton:hover {
                background-color: #374151;
            }
        """)

        # Main Text Area
        self.editor = QTextEdit()
        # Clean placeholders and styling
        self.editor.setPlaceholderText("Begin writing your masterpiece...")
        self.setCentralWidget(self.editor)

        self.current_file = None
        self.setup_toolbar()

    def setup_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # New File
        new_action = QAction("New", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_file)
        toolbar.addAction(new_action)

        # Open File
        open_action = QAction("Open", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file)
        toolbar.addAction(open_action)

        # Save File
        save_action = QAction("Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_file)
        toolbar.addAction(save_action)

        toolbar.addSeparator()

        # Clear
        clear_action = QAction("Clear", self)
        clear_action.triggered.connect(self.editor.clear)
        toolbar.addAction(clear_action)

    def new_file(self):
        # We can implement a check here to save before clearing if needed
        self.editor.clear()
        self.current_file = None
        self.setWindowTitle("Ghost Writer - Untitled")

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Text File", "", "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.editor.setPlainText(content)
                self.current_file = file_path
                self.setWindowTitle(f"Ghost Writer - {os.path.basename(file_path)}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not read file:\\n{str(e)}")

    def save_file(self):
        if not self.current_file:
            # Trigger Save As
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save File", "", "Text Files (*.txt);;All Files (*)"
            )
            if not file_path:
                return # User cancelled
            self.current_file = file_path

        try:
            with open(self.current_file, 'w', encoding='utf-8') as f:
                f.write(self.editor.toPlainText())
            self.setWindowTitle(f"Ghost Writer - {os.path.basename(self.current_file)}")
            # Optional: show a small non-intrusive status bar message for perfection
            self.statusBar().showMessage("File saved successfully.", 3000)
            self.statusBar().setStyleSheet("color: #9ca3af; background-color: #1f2937;")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save file:\\n{str(e)}")

def main():
    app = QApplication(sys.argv)
    
    # Enable high DPI scaling for crisp rendering
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    window = GhostWriterApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
