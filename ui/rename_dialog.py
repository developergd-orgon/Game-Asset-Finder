"""
RenameDialog  — lets the user rename a file or choose a new location for it.
"""
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QDialogButtonBox, QFileDialog, QTabWidget, QWidget,
)

from models.asset import Asset


class RenameDialog(QDialog):
    """Two-tab dialog: Rename | Move."""

    def __init__(self, asset: Asset, parent=None):
        super().__init__(parent)
        self.asset = asset
        self.new_stem: str | None = None
        self.new_folder: Path | None = None
        self.setWindowTitle(f"Rename / Move — {asset.name}")
        self.setMinimumWidth(460)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)

        tabs = QTabWidget()

        # ── Rename tab ────────────────────────────────────────────────────────
        rename_w = QWidget()
        rv = QVBoxLayout(rename_w)
        rv.addWidget(QLabel(f"Current name:  <b>{self.asset.path.name}</b>"))
        rv.addWidget(QLabel("New filename (without extension):"))
        self._name_edit = QLineEdit(self.asset.name)
        self._name_edit.selectAll()
        rv.addWidget(self._name_edit)
        rv.addWidget(QLabel(
            f"Extension <b>{self.asset.extension}</b> will be kept automatically."))
        rv.addStretch()
        tabs.addTab(rename_w, "✏️  Rename")

        # ── Move tab ──────────────────────────────────────────────────────────
        move_w = QWidget()
        mv = QVBoxLayout(move_w)
        mv.addWidget(QLabel("Current folder:"))
        mv.addWidget(QLabel(str(self.asset.path.parent)))
        mv.addWidget(QLabel("Destination folder:"))
        dest_row = QHBoxLayout()
        self._dest_edit = QLineEdit(str(self.asset.path.parent))
        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self._browse)
        dest_row.addWidget(self._dest_edit, 1)
        dest_row.addWidget(browse_btn)
        mv.addLayout(dest_row)
        mv.addStretch()
        tabs.addTab(move_w, "📁  Move")

        root.addWidget(tabs)
        self._tabs = tabs

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._apply)
        btns.rejected.connect(self.reject)
        root.addWidget(btns)

    def _browse(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Choose destination folder",
            str(self.asset.path.parent))
        if folder:
            self._dest_edit.setText(folder)

    def _apply(self):
        tab = self._tabs.currentIndex()
        if tab == 0:
            stem = self._name_edit.text().strip()
            if not stem:
                return
            self.new_stem = stem
        else:
            folder = Path(self._dest_edit.text().strip())
            if not folder or not folder != self.asset.path.parent:
                self.reject()
                return
            self.new_folder = folder
        self.accept()
