"""
AssetListPanel — left/centre panel: search bar, filters, asset table.
"""
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QColor, QIcon
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox,
    QTreeWidget, QTreeWidgetItem, QPushButton, QLabel,
    QSizePolicy, QToolButton, QMenu,
)

from models.asset import Asset, FILE_TYPES, ALL_TAG_CATEGORIES
from utils.library import Library


TYPE_ICONS = {
    "Images": "🖼", "Audio": "🎵", "Fonts": "🔤",
    "Video": "🎬", "3D": "🎲", "Data": "📄",
    "Code": "💻", "Archive": "📦", "Other": "📁",
}


class AssetListPanel(QWidget):
    asset_selected = Signal(object)      # emits Asset or None
    open_file      = Signal(object)      # double-click → open in default app
    edit_tags      = Signal(object)
    rename_move    = Signal(object)

    def __init__(self, library: Library, parent=None):
        super().__init__(parent)
        self._lib = library
        self._active_tag_filters: list[str] = []
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        # ── Top bar ───────────────────────────────────────────────────────────
        top = QHBoxLayout()
        self._search = QLineEdit()
        self._search.setPlaceholderText("🔍  Search by name, path or tag…")
        self._search.setClearButtonEnabled(True)
        self._search.textChanged.connect(self._do_filter)
        top.addWidget(self._search, 1)

        self._type_combo = QComboBox()
        self._type_combo.addItem("All types")
        for t in FILE_TYPES:
            self._type_combo.addItem(f"{TYPE_ICONS.get(t,'')}  {t}")
        self._type_combo.currentIndexChanged.connect(self._do_filter)
        top.addWidget(self._type_combo)
        root.addLayout(top)

        # ── Tag filter chips ──────────────────────────────────────────────────
        chip_row = QHBoxLayout()
        chip_row.setSpacing(4)
        chip_row.addWidget(QLabel("Filter tags:"))

        tag_btn = QToolButton()
        tag_btn.setText("+ Add tag filter ▾")
        tag_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._tag_menu = QMenu(tag_btn)
        for cat, tags in ALL_TAG_CATEGORIES.items():
            sub = self._tag_menu.addMenu(cat)
            for t in tags:
                act = sub.addAction(t)
                act.setCheckable(True)
                act.triggered.connect(lambda checked, tag=t: self._toggle_tag_filter(tag))
        tag_btn.setMenu(self._tag_menu)
        chip_row.addWidget(tag_btn)

        self._chip_area = QHBoxLayout()
        self._chip_area.setSpacing(4)
        chip_row.addLayout(self._chip_area)
        chip_row.addStretch()

        clear_tags = QPushButton("✕ Clear")
        clear_tags.setFixedHeight(24)
        clear_tags.clicked.connect(self._clear_tag_filters)
        chip_row.addWidget(clear_tags)

        root.addLayout(chip_row)

        # ── Count label ───────────────────────────────────────────────────────
        self._count_lbl = QLabel()
        self._count_lbl.setStyleSheet("color:#888; font-size:11px;")
        root.addWidget(self._count_lbl)

        # ── Tree widget ───────────────────────────────────────────────────────
        self._tree = QTreeWidget()
        self._tree.setColumnCount(4)
        self._tree.setHeaderLabels(["Name", "Type", "Size", "Tags"])
        self._tree.setColumnWidth(0, 240)
        self._tree.setColumnWidth(1, 70)
        self._tree.setColumnWidth(2, 60)
        self._tree.setAlternatingRowColors(True)
        self._tree.setRootIsDecorated(False)
        self._tree.setSortingEnabled(True)
        self._tree.currentItemChanged.connect(self._on_selection)
        self._tree.itemDoubleClicked.connect(self._on_double_click)
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._context_menu)
        root.addWidget(self._tree, 1)

    # ── Public ────────────────────────────────────────────────────────────────
    def refresh(self):
        self._do_filter()

    # ── Filtering ─────────────────────────────────────────────────────────────
    def _do_filter(self):
        text = self._search.text().strip()
        idx  = self._type_combo.currentIndex()
        ftype = "" if idx == 0 else list(FILE_TYPES.keys())[idx - 1]

        assets = self._lib.filter(
            text=text,
            file_type=ftype,
            tags=self._active_tag_filters if self._active_tag_filters else None,
        )
        self._populate(assets)

    def _populate(self, assets: list[Asset]):
        self._tree.setUpdatesEnabled(False)
        self._tree.clear()
        for a in assets:
            item = QTreeWidgetItem([
                a.name,
                f"{TYPE_ICONS.get(a.file_type,'')} {a.file_type}",
                a.size_str,
                ", ".join(a.all_tags()) or "—",
            ])
            item.setData(0, Qt.ItemDataRole.UserRole, a)
            item.setToolTip(0, str(a.path))
            self._tree.addTopLevelItem(item)
        self._tree.setUpdatesEnabled(True)
        self._count_lbl.setText(f"{len(assets)} asset{'s' if len(assets)!=1 else ''}")

    # ── Tag chip helpers ──────────────────────────────────────────────────────
    def _toggle_tag_filter(self, tag: str):
        if tag in self._active_tag_filters:
            self._active_tag_filters.remove(tag)
        else:
            self._active_tag_filters.append(tag)
        self._rebuild_chips()
        self._do_filter()

    def _clear_tag_filters(self):
        self._active_tag_filters.clear()
        for act in self._tag_menu.actions():
            menu = act.menu()
            if menu:
                for a in menu.actions():
                    a.setChecked(False)
        self._rebuild_chips()
        self._do_filter()

    def _rebuild_chips(self):
        # clear old chips
        while self._chip_area.count():
            item = self._chip_area.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for tag in self._active_tag_filters:
            btn = QPushButton(f"{tag}  ✕")
            btn.setFixedHeight(22)
            btn.setStyleSheet(
                "QPushButton{background:#2d4a7a;color:#fff;"
                "border-radius:11px;padding:0 8px;font-size:11px;}"
                "QPushButton:hover{background:#c0392b;}"
            )
            btn.clicked.connect(lambda _, t=tag: self._toggle_tag_filter(t))
            self._chip_area.addWidget(btn)

    # ── Slots ─────────────────────────────────────────────────────────────────
    def _on_selection(self, current, _previous):
        asset = current.data(0, Qt.ItemDataRole.UserRole) if current else None
        self.asset_selected.emit(asset)

    def _on_double_click(self, item, _col):
        asset = item.data(0, Qt.ItemDataRole.UserRole)
        if asset:
            self.open_file.emit(asset)

    def _context_menu(self, pos):
        item = self._tree.itemAt(pos)
        if not item:
            return
        asset = item.data(0, Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        menu.addAction("🔖  Edit tags…").triggered.connect(lambda: self.edit_tags.emit(asset))
        menu.addAction("✏️  Rename / Move…").triggered.connect(lambda: self.rename_move.emit(asset))
        menu.addSeparator()
        menu.addAction("📂  Show in file manager").triggered.connect(
            lambda: self._reveal(asset))
        menu.exec(self._tree.viewport().mapToGlobal(pos))

    @staticmethod
    def _reveal(asset: Asset):
        import subprocess, sys
        p = str(asset.path.parent)
        if sys.platform == "win32":
            subprocess.Popen(["explorer", "/select,", str(asset.path)])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", "-R", str(asset.path)])
        else:
            subprocess.Popen(["xdg-open", p])
