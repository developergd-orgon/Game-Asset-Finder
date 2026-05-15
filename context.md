# Contexto del Proyecto: Game Asset Finder

## ¿Qué es este proyecto?
Game Asset Finder es una aplicación de escritorio multiplataforma escrita en Python con PySide6. Su propósito es ayudar a desarrolladores indie y hobbyistas a escanear carpetas locales, previsualizar archivos y organizar sus assets de videojuego mediante un sistema de etiquetas.

---

## Stack tecnológico
- **Lenguaje:** Python 3.9+
- **GUI:** PySide6 (Qt6 para Python)
- **Audio/Video:** QMediaPlayer (incluido en PySide6)
- **Persistencia:** JSON local en `~/.asset-finder/library.json`
- **Empaquetado recomendado:** PyInstaller
- **Licencia:** MIT

---

## Estructura de archivos

```
asset-finder/
├── main.py                    # Punto de entrada
├── requirements.txt           # PySide6>=6.6.0, Pillow>=10.0.0
├── LICENSE
├── README.md
├── models/
│   └── asset.py               # Dataclass Asset + taxonomía de tags + grupos de tipos
├── utils/
│   └── library.py             # Escaneo, persistencia, filtrado, rename/move
└── ui/
    ├── main_window.py          # Ventana principal, toolbar, menú
    ├── asset_list.py           # Barra de búsqueda, filtros, chips de tags, tabla
    ├── preview_panel.py        # Preview de imagen / audio / genérico
    ├── tag_editor.py           # Diálogo de edición de tags
    └── rename_dialog.py        # Diálogo de renombrar / mover
```

---

## Módulo: `models/asset.py`

### Clase `Asset` (dataclass)
| Campo | Tipo | Descripción |
|---|---|---|
| `path` | `Path` | Ruta absoluta al archivo en disco |
| `name` | `str` | Nombre sin extensión (editable por el usuario) |
| `file_type` | `str` | Grupo: Images, Audio, Fonts, etc. |
| `tags` | `dict` | `{Genre: [], Mood: [], Situation: [], Mechanic: []}` |
| `notes` | `str` | Notas libres del usuario |

**Métodos clave:**
- `all_tags() → list[str]` — aplana todos los tags de todas las categorías
- `size_str → str` — tamaño del archivo formateado (B, KB, MB, GB)
- `to_dict() / from_dict()` — serialización JSON

### Tipos de archivo soportados
| Grupo | Extensiones |
|---|---|
| Images | `.png .jpg .jpeg .gif .bmp .webp .tga .tiff .svg` |
| Audio | `.mp3 .wav .ogg .flac .aac .opus .m4a` |
| Fonts | `.ttf .otf .woff .woff2` |
| Video | `.mp4 .avi .mov .mkv .webm` |
| 3D | `.obj .fbx .gltf .glb .blend .stl` |
| Data | `.json .xml .csv .yaml .toml` |
| Code | `.py .gd .cs .lua .js .ts .cpp .h` |
| Archive | `.zip .tar .gz .rar .7z` |

### Sistema de tags — taxonomía completa
```python
GENRE_TAGS     = ["RPG","Platformer","Puzzle","Horror","Sci-Fi","Fantasy",
                   "Western","Space","Dungeon","Shooter","Racing","Sports",
                   "Stealth","Survival","Adventure","Casual"]

MOOD_TAGS      = ["Epic","Calm","Dark","Upbeat","Mysterious","Tense",
                   "Melancholic","Joyful","Creepy","Dramatic","Peaceful",
                   "Chaotic","Romantic","Nostalgic"]

SITUATION_TAGS = ["Boss Fight","Exploration","Menu / Title","Game Over",
                   "Victory","Cutscene","Ambiance","Intro","Loading",
                   "Tutorial","Level Complete","Shop","Chase","Stealth"]

MECHANIC_TAGS  = ["Jump","Attack","Pickup","Footstep","Explosion","Magic",
                   "UI Click","UI Hover","Notification","Door","Ambient Loop",
                   "Voice / Narration","Environment","Vehicle"]
```

---

## Módulo: `utils/library.py`

### Clase `Library`
Gestiona todos los assets en memoria y en disco.

| Método | Descripción |
|---|---|
| `scan_folder(folder, recursive, progress_cb)` | Escanea una carpeta, agrega assets nuevos, llama `progress_cb(n, filename)` |
| `save()` | Persiste la librería a `~/.asset-finder/library.json` |
| `all_assets() → list[Asset]` | Devuelve todos los assets |
| `filter(text, file_type, tags)` | Filtra por texto, tipo y/o lista de tags |
| `rename_file(asset, new_stem) → Asset` | Renombra el archivo en disco y actualiza la librería |
| `move_file(asset, dest_folder) → Asset` | Mueve el archivo en disco y actualiza la librería |
| `update(asset)` | Actualiza un asset (por ejemplo tras editar tags) y guarda |
| `remove(asset)` | Elimina un asset de la librería |

---

## Módulo: `ui/main_window.py`

- `MainWindow(QMainWindow)` — ventana principal
- Usa `QSplitter` horizontal: `AssetListPanel` (izquierda, ratio 2) + `PreviewPanel` (derecha, ratio 1)
- Toolbar con botones **Scan Folder** y **Refresh** + contador de assets
- Menú: File, Asset, Help
- Lanza escaneo en hilo separado (`ScanWorker(QObject)` + `QThread`) con `QProgressDialog`
- Estilos: dark theme inspirado en GitHub Dark, aplicado como stylesheet global

**Atajos de teclado:**
| Atajo | Acción |
|---|---|
| `Ctrl+O` | Escanear carpeta |
| `Ctrl+R` | Refrescar lista |
| `Ctrl+T` | Editar tags del asset seleccionado |
| `F2` | Renombrar / Mover |
| Doble clic | Abrir en aplicación del sistema |

---

## Módulo: `ui/asset_list.py`

- `AssetListPanel(QWidget)`
- **Señales emitidas:** `asset_selected(Asset)`, `open_file(Asset)`, `edit_tags(Asset)`, `rename_move(Asset)`
- Barra de búsqueda con `QLineEdit` (busca en nombre, ruta y tags)
- `QComboBox` para filtrar por tipo de archivo
- Sistema de chips de tags: menú desplegable por categoría → chips inline con botón ✕
- `QTreeWidget` con columnas: Nombre, Tipo, Tamaño, Tags
- Menú contextual (clic derecho): Editar tags, Renombrar/Mover, Mostrar en explorador

---

## Módulo: `ui/preview_panel.py`

- `PreviewPanel(QWidget)`
- Método público: `load_asset(asset: Asset | None)`
- **Imágenes:** renderiza con `QPixmap`, escalado `KeepAspectRatio`
- **Audio:** muestra controles `▶ Play / ⏸ Pause / ■ Stop`, `QSlider` de seek, `QSlider` de volumen — usa `QMediaPlayer` + `QAudioOutput`
- **Otros tipos:** ícono emoji según grupo
- Se recalcula el tamaño de imagen al hacer resize de la ventana

---

## Módulo: `ui/tag_editor.py`

- `TagEditorDialog(QDialog)`
- Muestra un `QGroupBox` por cada categoría con `QCheckBox` por tag (grid de 4 columnas)
- Campo `QTextEdit` para notas libres
- Al aceptar, escribe los tags seleccionados de vuelta en `asset.tags`

---

## Módulo: `ui/rename_dialog.py`

- `RenameDialog(QDialog)`
- Dos pestañas: **Rename** (edita el stem, conserva extensión) y **Move** (selector de carpeta destino)
- Expone `dlg.new_stem: str | None` y `dlg.new_folder: Path | None` tras `exec()`

---

## Persistencia
- Archivo: `~/.asset-finder/library.json`
- Formato: array JSON de objetos `Asset.to_dict()`
- Al cargar, se descartan entradas cuyo `path` ya no existe en disco
- Se guarda automáticamente tras cada operación (scan, update, rename, move, remove)

---

## Decisiones de diseño importantes
1. **Sin base de datos** — JSON plano para cero dependencias extra y portabilidad total.
2. **Scan incremental** — solo agrega archivos nuevos; no borra entradas existentes aunque ya no estén en el directorio escaneado (se limpian al cargar).
3. **Hilo de escaneo** — `ScanWorker` corre en `QThread` para no bloquear la UI.
4. **Tags como listas de strings** — simple, serializable, fácil de filtrar.
5. **Rename/Move en disco** — la librería actualiza la clave del diccionario (`str(path)`) para mantener consistencia.

---

## Instalación y ejecución
```bash
pip install PySide6>=6.6.0 Pillow>=10.0.0
python main.py
```

## Empaquetado
```bash
pip install pyinstaller
pyinstaller --onefile --windowed \
  --hidden-import=PySide6.QtMultimedia \
  --name "GameAssetFinder" main.py
```

---

## Posibles mejoras futuras (backlog)
- Soporte de miniaturas en grid view
- Exportar lista de assets a CSV
- Importar/exportar tags entre proyectos
- Soporte de colecciones / carpetas virtuales
- Integración con itch.io / OpenGameArt para buscar assets online
- Preview de fuentes con texto personalizable
- Preview de archivos 3D (visor básico)
- Drag & drop para mover assets entre carpetas
- Tema claro opcional