# 🎮 Game Asset Finder

A cross-platform desktop app for game developers to **scan, preview, tag, rename and organise** local asset files.

---

## Features

| Feature | Details |
|---|---|
| **Folder scanning** | Recursively scans any folder and indexes all game-relevant files |
| **File type filter** | Images, Audio, Fonts, Video, 3D, Data, Code, Archive |
| **Live search** | Fuzzy search by filename, path or tag |
| **Tag system** | Four categories: Genre, Mood, Situation, Mechanic |
| **Tag filter chips** | Click tags to narrow results, stacked filters supported |
| **Image preview** | Click any image asset to see it in the preview panel |
| **Audio playback** | Built-in play/pause/seek/volume controls for audio files |
| **Rename** | Rename files on disk with one dialog, no extension fumbling |
| **Move** | Relocate files to a different folder from inside the app |
| **Persistent library** | Metadata and tags saved to `~/.asset-finder/library.json` |
| **Dark theme** | GitHub-dark inspired, easy on the eyes |

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note:** `PySide6` requires Python 3.9+.  
> On Linux you may also need: `sudo apt install libgstreamer1.0-dev gstreamer1.0-plugins-base`

### 2. Run

```bash
python main.py
```

### 3. Scan a folder

Click **📂 Scan Folder** in the toolbar, choose a directory, and the app will recursively index all supported files.

---

## Tag System

Four independent categories, each with curated presets:

| Category | Examples |
|---|---|
| **Genre** | RPG, Platformer, Horror, Sci-Fi, Dungeon… |
| **Mood** | Epic, Dark, Mysterious, Calm, Tense… |
| **Situation** | Boss Fight, Exploration, Menu / Title, Victory… |
| **Mechanic** | Jump, Attack, Explosion, UI Click, Ambient Loop… |

Right-click any asset → **Edit tags…** or press `Ctrl+T`.

---

## Keyboard Shortcuts

| Key | Action |
|---|---|
| `Ctrl+O` | Scan folder |
| `Ctrl+R` | Refresh list |
| `Ctrl+T` | Edit tags for selected asset |
| `F2` | Rename / Move selected asset |
| Double-click | Open file in default system app |

---

## Packaging (optional)

```bash
pip install pyinstaller
pyinstaller --onefile --windowed \
  --hidden-import=PySide6.QtMultimedia \
  --name "GameAssetFinder" \
  main.py
```

Output binary will be in `dist/`.

---

## Project Structure

```
asset-finder/
├── main.py                  # Entry point
├── requirements.txt
├── models/
│   └── asset.py             # Asset dataclass + tag taxonomy + file-type groups
├── utils/
│   └── library.py           # Scan, persist, filter, rename, move
└── ui/
    ├── main_window.py        # Top-level window, toolbar, menu
    ├── asset_list.py         # Search bar, type filter, tag chips, tree view
    ├── preview_panel.py      # Image / audio / generic preview
    ├── tag_editor.py         # Tag editing dialog
    └── rename_dialog.py      # Rename / Move dialog
```

---

## Supported File Types

| Group | Extensions |
|---|---|
| Images | `.png .jpg .jpeg .gif .bmp .webp .tga .tiff .svg` |
| Audio | `.mp3 .wav .ogg .flac .aac .opus .m4a` |
| Fonts | `.ttf .otf .woff .woff2` |
| Video | `.mp4 .avi .mov .mkv .webm` |
| 3D | `.obj .fbx .gltf .glb .blend .stl` |
| Data | `.json .xml .csv .yaml .toml` |
| Code | `.py .gd .cs .lua .js .ts .cpp .h` |
| Archive | `.zip .tar .gz .rar .7z` |
