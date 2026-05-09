"""
TagEditorDialog — modal dialog for editing an asset's tags and notes.
"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QTextEdit, QScrollArea, QWidget, QGroupBox,
    QGridLayout, QDialogButtonBox,
)

from models.asset import ALL_TAG_CATEGORIES, Asset


class TagEditorDialog(QDialog):
    def __init__(self, asset: Asset, parent=None):
        super().__init__(parent)
        self.asset = asset
        self.setWindowTitle(f"Tags — {asset.name}")
        self.setMinimumSize(540, 520)
        self._checkboxes: dict[str, QCheckBox] = {}
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(10)

        header = QLabel(f"Editing tags for: <b>{self.asset.name}</b>")
        header.setTextFormat(Qt.TextFormat.RichText)
        root.addWidget(header)

        # ── Scrollable tag area ───────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(scroll.Shape.NoFrame)
        inner = QWidget()
        iv = QVBoxLayout(inner)
        iv.setSpacing(12)

        for category, tags in ALL_TAG_CATEGORIES.items():
            box = QGroupBox(category)
            box.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            grid = QGridLayout(box)
            grid.setSpacing(4)
            current = self.asset.tags.get(category, [])
            for i, tag in enumerate(tags):
                cb = QCheckBox(tag)
                cb.setChecked(tag in current)
                grid.addWidget(cb, i // 4, i % 4)
                self._checkboxes[f"{category}::{tag}"] = cb
            iv.addWidget(box)

        scroll.setWidget(inner)
        root.addWidget(scroll, 1)

        # ── Notes ─────────────────────────────────────────────────────────────
        root.addWidget(QLabel("Notes:"))
        self._notes = QTextEdit()
        self._notes.setPlainText(self.asset.notes)
        self._notes.setMaximumHeight(80)
        root.addWidget(self._notes)

        # ── Buttons ───────────────────────────────────────────────────────────
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._apply)
        btns.rejected.connect(self.reject)
        root.addWidget(btns)

    def _apply(self):
        for category in ALL_TAG_CATEGORIES:
            selected = []
            for tag in ALL_TAG_CATEGORIES[category]:
                cb = self._checkboxes.get(f"{category}::{tag}")
                if cb and cb.isChecked():
                    selected.append(tag)
            self.asset.tags[category] = selected
        self.asset.notes = self._notes.toPlainText().strip()
        self.accept()
