"""
main.py — entry point for Game Asset Finder.
"""
import sys
from pathlib import Path

# Make sure sibling packages are importable regardless of CWD
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Game Asset Finder")
    app.setApplicationVersion("1.0")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
