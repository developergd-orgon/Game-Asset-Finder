"""
PreviewPanel — right-side panel that shows an image, plays audio,
or displays file info depending on the selected asset's type.
"""
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QSizePolicy, QFrame, QTextEdit,
)

from models.asset import Asset


class PreviewPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._asset: Asset | None = None
        self._player = QMediaPlayer(self)
        self._audio_out = QAudioOutput(self)
        self._player.setAudioOutput(self._audio_out)
        self._audio_out.setVolume(0.8)
        self._player.playbackStateChanged.connect(self._on_playback_changed)
        self._player.durationChanged.connect(self._on_duration_changed)
        self._player.positionChanged.connect(self._on_position_changed)
        self._build_ui()

    # ── Build UI ──────────────────────────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        # ── Title bar ────────────────────────────────────────────────────────
        self._title = QLabel("No asset selected")
        self._title.setWordWrap(True)
        self._title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self._title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        root.addWidget(self._title)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        root.addWidget(sep)

        # ── Image area ───────────────────────────────────────────────────────
        self._image_label = QLabel()
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_label.setMinimumHeight(200)
        self._image_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._image_label.setStyleSheet(
            "background:#1a1a2e; border-radius:8px;")
        root.addWidget(self._image_label, 1)

        # ── Audio controls ───────────────────────────────────────────────────
        self._audio_widget = QWidget()
        av = QVBoxLayout(self._audio_widget)
        av.setContentsMargins(0, 0, 0, 0)

        audio_icon = QLabel("🎵")
        audio_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        audio_icon.setFont(QFont("Segoe UI", 36))
        av.addWidget(audio_icon)

        self._seek = QSlider(Qt.Orientation.Horizontal)
        self._seek.setRange(0, 0)
        self._seek.sliderMoved.connect(self._player.setPosition)
        av.addWidget(self._seek)

        ctl = QHBoxLayout()
        self._play_btn = QPushButton("▶  Play")
        self._play_btn.setFixedHeight(36)
        self._play_btn.clicked.connect(self._toggle_play)
        self._stop_btn = QPushButton("■  Stop")
        self._stop_btn.setFixedHeight(36)
        self._stop_btn.clicked.connect(self._player.stop)
        self._time_lbl = QLabel("0:00 / 0:00")
        ctl.addWidget(self._play_btn)
        ctl.addWidget(self._stop_btn)
        ctl.addWidget(self._time_lbl)
        av.addLayout(ctl)

        vol_row = QHBoxLayout()
        vol_row.addWidget(QLabel("🔊"))
        self._vol_slider = QSlider(Qt.Orientation.Horizontal)
        self._vol_slider.setRange(0, 100)
        self._vol_slider.setValue(80)
        self._vol_slider.valueChanged.connect(
            lambda v: self._audio_out.setVolume(v / 100))
        vol_row.addWidget(self._vol_slider)
        av.addLayout(vol_row)

        root.addWidget(self._audio_widget)
        self._audio_widget.hide()

        # ── File info ────────────────────────────────────────────────────────
        self._info = QTextEdit()
        self._info.setReadOnly(True)
        self._info.setMaximumHeight(90)
        self._info.setStyleSheet("background:#0d1117; border-radius:6px; color:#aaa; font-size:11px;")
        root.addWidget(self._info)

    # ── Public API ────────────────────────────────────────────────────────────
    def load_asset(self, asset: Asset | None):
        self._player.stop()
        self._asset = asset
        self._audio_widget.hide()
        self._image_label.setPixmap(QPixmap())
        self._image_label.setText("")

        if asset is None:
            self._title.setText("No asset selected")
            self._info.clear()
            return

        self._title.setText(asset.name)

        ftype = asset.file_type
        path  = asset.path

        if ftype == "Images":
            self._show_image(path)
        elif ftype in ("Audio",):
            self._show_audio(path)
        elif ftype == "Fonts":
            self._show_font_preview(path)
        else:
            self._show_generic(path)

        self._info.setPlainText(
            f"Path:  {path}\n"
            f"Type:  {ftype}  ({asset.extension})\n"
            f"Size:  {asset.size_str}\n"
            f"Tags:  {', '.join(asset.all_tags()) or '—'}"
        )

    # ── Private helpers ───────────────────────────────────────────────────────
    def _show_image(self, path: Path):
        px = QPixmap(str(path))
        if px.isNull():
            self._image_label.setText("⚠ Cannot load image")
        else:
            self._image_label.setPixmap(
                px.scaled(self._image_label.width() or 400,
                           self._image_label.height() or 300,
                           Qt.AspectRatioMode.KeepAspectRatio,
                           Qt.TransformationMode.SmoothTransformation))

    def _show_audio(self, path: Path):
        self._audio_widget.show()
        self._image_label.setText("🎵")
        self._player.setSource(QUrl.fromLocalFile(str(path)))

    def _show_font_preview(self, path: Path):
        self._image_label.setText("Aa Bb Cc\n123 !@#")
        self._image_label.setFont(QFont(str(path), 28))

    def _show_generic(self, path: Path):
        ext_icons = {
            "Video": "🎬", "3D": "🎲", "Data": "📄",
            "Code": "💻", "Archive": "📦",
        }
        icon = ext_icons.get(self._asset.file_type if self._asset else "", "📁")
        self._image_label.setText(icon)
        self._image_label.setFont(QFont("Segoe UI", 48))

    # ── Playback slots ────────────────────────────────────────────────────────
    def _toggle_play(self):
        if self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._player.pause()
        else:
            self._player.play()

    def _on_playback_changed(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self._play_btn.setText("⏸  Pause")
        else:
            self._play_btn.setText("▶  Play")

    def _on_duration_changed(self, ms: int):
        self._seek.setMaximum(ms)
        self._time_lbl.setText(f"0:00 / {self._ms_fmt(ms)}")

    def _on_position_changed(self, ms: int):
        self._seek.setValue(ms)
        dur = self._player.duration()
        self._time_lbl.setText(f"{self._ms_fmt(ms)} / {self._ms_fmt(dur)}")

    @staticmethod
    def _ms_fmt(ms: int) -> str:
        s = ms // 1000
        return f"{s // 60}:{s % 60:02d}"

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        if self._asset and self._asset.file_type == "Images":
            self._show_image(self._asset.path)
