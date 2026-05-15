"""
MainWindow — top-level QMainWindow that wires panels and the library together.
"""
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal, QObject
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QSplitter, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QMessageBox,
    QStatusBar, QProgressDialog, QApplication, QToolBar,
)

from models.asset import Asset
from utils.library import Library
from ui.asset_list import AssetListPanel
from ui.preview_panel import PreviewPanel
from ui.tag_editor import TagEditorDialog
from ui.rename_dialog import RenameDialog


# ── Background scan worker ────────────────────────────────────────────────────
class ScanWorker(QObject):
    progress = Signal(int, str)
    finished = Signal(int)

    def __init__(self, library: Library, folder: Path, recursive: bool):
        super().__init__()
        self._lib  = library
        self._folder = folder
        self._recursive = recursive

    def run(self):
        count = self._lib.scan_folder(
            self._folder,
            recursive=self._recursive,
            progress_cb=self.progress.emit,
        )
        self.finished.emit(count)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._lib = Library()
        self._current_asset: Asset | None = None
        self.setWindowTitle("🎮 Game Asset Finder")
        self.resize(1200, 700)
        self._build_ui()
        self._build_menu()
        self.setStyleSheet(STYLE)

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Central splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        self._list_panel = AssetListPanel(self._lib)
        self._preview    = PreviewPanel()

        splitter.addWidget(self._list_panel)
        splitter.addWidget(self._preview)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([800, 400])

        self.setCentralWidget(splitter)

        # Status bar
        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status.showMessage("Ready — scan a folder to get started.")

        # Toolbar
        tb = QToolBar("Main")
        tb.setMovable(False)
        self.addToolBar(tb)

        scan_btn = QPushButton("📂  Scan Folder")
        scan_btn.clicked.connect(self._scan_dialog)
        tb.addWidget(scan_btn)

        refresh_btn = QPushButton("🔄  Refresh")
        refresh_btn.clicked.connect(self._refresh)
        tb.addWidget(refresh_btn)

        tb.addSeparator()

        lbl = QLabel(f"  {len(self._lib.all_assets())} assets in library  ")
        lbl.setStyleSheet("color:#aaa; font-size:11px;")
        self._count_toolbar_lbl = lbl
        tb.addWidget(lbl)

        # Wire signals
        self._list_panel.asset_selected.connect(self._on_asset_selected)
        self._list_panel.open_file.connect(self._open_in_app)
        self._list_panel.edit_tags.connect(self._edit_tags)
        self._list_panel.rename_move.connect(self._rename_move)
        self._list_panel.remove_asset.connect(self._on_remove_asset)
        self._list_panel.toggle_ignore.connect(self._on_toggle_ignore)

    def _build_menu(self):
        mb = self.menuBar()

        file_m = mb.addMenu("&File")
        file_m.addAction("📂  Scan Folder…", self._scan_dialog, "Ctrl+O")
        file_m.addAction("🔄  Refresh library", self._refresh, "Ctrl+R")
        file_m.addSeparator()
        file_m.addAction("Quit", self.close, "Ctrl+Q")

        asset_m = mb.addMenu("&Asset")
        asset_m.addAction("🔖  Edit tags…", self._edit_current_tags, "Ctrl+T")
        asset_m.addAction("✏️  Rename / Move…", self._rename_current, "F2")
        asset_m.addAction("📂  Show in file manager", self._reveal_current)
        asset_m.addSeparator()
        asset_m.addAction("🚫  Ignore", self._on_toggle_ignore, "Ctrl+I")
        asset_m.addAction("🗑  Remove from library", self._on_remove_asset, "Ctrl+D")

        help_m = mb.addMenu("&Help")
        help_m.addAction("About", self._about)

    # ── Slots ─────────────────────────────────────────────────────────────────
    def _on_asset_selected(self, asset):
        self._current_asset = asset
        self._preview.load_asset(asset)
        if asset:
            self._status.showMessage(str(asset.path))

    def _scan_dialog(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose folder to scan")
        if not folder:
            return
        self._run_scan(Path(folder))

    def _run_scan(self, folder: Path):
        self._progress = QProgressDialog("Scanning…", "Cancel", 0, 0, self)
        self._progress.setWindowModality(Qt.WindowModality.WindowModal)
        self._progress.setMinimumDuration(0)
        self._progress.setValue(0)

        self._scan_thread = QThread(self)
        self._scan_worker = ScanWorker(self._lib, folder, recursive=True)
        self._scan_worker.moveToThread(self._scan_thread)
        self._scan_thread.started.connect(self._scan_worker.run)
        self._scan_worker.progress.connect(
            lambda _n, name: self._progress.setLabelText(f"Scanning: {name}"))
        self._scan_worker.finished.connect(self._on_scan_done)
        self._scan_worker.finished.connect(self._scan_thread.quit)
        self._scan_thread.start()
        self._progress.exec()

    def _on_scan_done(self, new_count: int):
        self._progress.close()
        self._refresh()
        total = len(self._lib.all_assets())
        self._status.showMessage(
            f"Scan complete — {new_count} new assets added. Total: {total}.")
        self._count_toolbar_lbl.setText(f"  {total} assets in library  ")

    def _refresh(self):
        self._list_panel.refresh()

    def _open_in_app(self, asset: Asset):
        try:
            if sys.platform == "win32":
                import os; os.startfile(str(asset.path))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(asset.path)])
            else:
                subprocess.Popen(["xdg-open", str(asset.path)])
        except Exception as e:
            QMessageBox.warning(self, "Open failed", str(e))

    def _edit_tags(self, asset: Asset):
        dlg = TagEditorDialog(asset, self)
        if dlg.exec():
            self._lib.update(asset)
            self._refresh()
            self._preview.load_asset(asset)
            self._status.showMessage(f"Tags saved for {asset.name}.")

    def _edit_current_tags(self):
        if self._current_asset:
            self._edit_tags(self._current_asset)

    def _rename_move(self, asset: Asset):
        dlg = RenameDialog(asset, self)
        if not dlg.exec():
            return
        try:
            if dlg.new_stem:
                self._lib.rename_file(asset, dlg.new_stem)
                self._status.showMessage(f"Renamed to {asset.path.name}.")
            elif dlg.new_folder:
                self._lib.move_file(asset, dlg.new_folder)
                self._status.showMessage(f"Moved to {asset.path.parent}.")
            self._refresh()
            self._preview.load_asset(asset)
        except FileExistsError as e:
            QMessageBox.warning(self, "Cannot rename / move", str(e))

    def _rename_current(self):
        if self._current_asset:
            self._rename_move(self._current_asset)

    def _reveal_current(self):
        if self._current_asset:
            AssetListPanel._reveal(self._current_asset)

    def _about(self):
        QMessageBox.about(
            self, "Game Asset Finder",
            "<b>Game Asset Finder</b><br>v1.0<br><br>"
            "Scan folders, tag, preview and organise your game assets.<br>"
            "Built with Python + PySide6."
        )
        
    def _on_remove_asset(self, asset: Asset) -> None:
        self._lib.remove(asset)
        self._list_panel.refresh()

    def _on_toggle_ignore(self, asset: Asset) -> None:
        self._lib.toggle_ignore(asset)
        self._list_panel.refresh()



# ── Stylesheet ────────────────────────────────────────────────────────────────
STYLE = """
QMainWindow, QWidget {
    background-color: #0d1117;
    color: #e6edf3;
    font-family: 'Segoe UI', 'Inter', sans-serif;
    font-size: 12px;
}
QMenuBar { background:#161b22; color:#e6edf3; padding:2px; }
QMenuBar::item:selected { background:#21262d; }
QMenu { background:#21262d; border:1px solid #30363d; }
QMenu::item:selected { background:#388bfd; color:#fff; }
QToolBar { background:#161b22; border-bottom:1px solid #30363d; padding:4px; spacing:6px; }
QPushButton {
    background:#21262d; color:#e6edf3;
    border:1px solid #30363d; border-radius:6px;
    padding:5px 12px;
}
QPushButton:hover { background:#30363d; border-color:#58a6ff; }
QPushButton:pressed { background:#0d1117; }
QLineEdit, QComboBox, QTextEdit {
    background:#0d1117; color:#e6edf3;
    border:1px solid #30363d; border-radius:5px; padding:4px 8px;
}
QLineEdit:focus, QComboBox:focus { border-color:#58a6ff; }
QComboBox QAbstractItemView { background:#21262d; selection-background-color:#388bfd; }
QTreeWidget {
    background:#0d1117; alternate-background-color:#161b22;
    border:1px solid #21262d;
}
QTreeWidget::item:selected { background:#1f3a6e; }
QTreeWidget::item:hover { background:#21262d; }
QHeaderView::section {
    background:#161b22; color:#8b949e;
    border:none; border-bottom:1px solid #30363d;
    padding:4px 6px;
}
QSplitter::handle { background:#21262d; width:2px; }
QScrollBar:vertical {
    background:#0d1117; width:8px; margin:0;
}
QScrollBar::handle:vertical { background:#30363d; border-radius:4px; min-height:20px; }
QScrollBar::add-line, QScrollBar::sub-line { height:0; }
QGroupBox {
    border:1px solid #30363d; border-radius:6px;
    margin-top:10px; padding-top:6px;
}
QGroupBox::title { color:#58a6ff; subcontrol-position:top left; left:10px; }
QSlider::groove:horizontal { background:#21262d; height:4px; border-radius:2px; }
QSlider::handle:horizontal {
    background:#58a6ff; width:12px; height:12px;
    border-radius:6px; margin:-4px 0;
}
QSlider::sub-page:horizontal { background:#388bfd; border-radius:2px; }
QDialog { background:#0d1117; }
QDialogButtonBox QPushButton { min-width:80px; }
QStatusBar { background:#161b22; color:#8b949e; border-top:1px solid #30363d; }
"""
