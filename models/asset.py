"""
Asset model — represents a single file on disk with metadata and tags.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ── Tag taxonomy ────────────────────────────────────────────────────────────
GENRE_TAGS = [
    "RPG", "Platformer", "Puzzle", "Horror", "Sci-Fi", "Fantasy",
    "Western", "Space", "Dungeon", "Shooter", "Racing", "Sports",
    "Stealth", "Survival", "Adventure", "Casual",
]

MOOD_TAGS = [
    "Epic", "Calm", "Dark", "Upbeat", "Mysterious", "Tense",
    "Melancholic", "Joyful", "Creepy", "Dramatic", "Peaceful",
    "Chaotic", "Romantic", "Nostalgic",
]

SITUATION_TAGS = [
    "Boss Fight", "Exploration", "Menu / Title", "Game Over",
    "Victory", "Cutscene", "Ambiance", "Intro", "Loading",
    "Tutorial", "Level Complete", "Shop", "Chase", "Stealth",
]

MECHANIC_TAGS = [
    "Jump", "Attack", "Pickup", "Footstep", "Explosion", "Magic",
    "UI Click", "UI Hover", "Notification", "Door", "Ambient Loop",
    "Voice / Narration", "Environment", "Vehicle",
]

ALL_TAG_CATEGORIES = {
    "Genre":     GENRE_TAGS,
    "Mood":      MOOD_TAGS,
    "Situation": SITUATION_TAGS,
    "Mechanic":  MECHANIC_TAGS,
}

# ── File-type groups ─────────────────────────────────────────────────────────
FILE_TYPES = {
    "Images":  {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tga", ".tiff", ".svg"},
    "Audio":   {".mp3", ".wav", ".ogg", ".flac", ".aac", ".opus", ".m4a"},
    "Fonts":   {".ttf", ".otf", ".woff", ".woff2"},
    "Video":   {".mp4", ".avi", ".mov", ".mkv", ".webm"},
    "3D":      {".obj", ".fbx", ".gltf", ".glb", ".blend", ".stl"},
    "Data":    {".json", ".xml", ".csv", ".yaml", ".toml"},
    "Code":    {".py", ".gd", ".cs", ".lua", ".js", ".ts", ".cpp", ".h"},
    "Archive": {".zip", ".tar", ".gz", ".rar", ".7z"},
}


def ext_to_group(ext: str) -> str:
    ext = ext.lower()
    for group, exts in FILE_TYPES.items():
        if ext in exts:
            return group
    return "Other"


@dataclass
class Asset:
    path: Path
    name: str = ""
    file_type: str = ""       # Images / Audio / Fonts …
    tags: dict = field(default_factory=lambda: {
        "Genre": [], "Mood": [], "Situation": [], "Mechanic": []
    })
    notes: str = ""

    def __post_init__(self):
        self.path = Path(self.path)
        if not self.name:
            self.name = self.path.stem
        if not self.file_type:
            self.file_type = ext_to_group(self.path.suffix)

    @property
    def extension(self) -> str:
        return self.path.suffix.lower()

    @property
    def size_str(self) -> str:
        try:
            b = self.path.stat().st_size
            for unit in ("B", "KB", "MB", "GB"):
                if b < 1024:
                    return f"{b:.1f} {unit}"
                b /= 1024
        except Exception:
            pass
        return "?"

    def all_tags(self) -> list[str]:
        out = []
        for lst in self.tags.values():
            out.extend(lst)
        return out

    def to_dict(self) -> dict:
        return {
            "path":      str(self.path),
            "name":      self.name,
            "file_type": self.file_type,
            "tags":      self.tags,
            "notes":     self.notes,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Asset":
        a = cls(path=d["path"])
        a.name      = d.get("name", a.path.stem)
        a.file_type = d.get("file_type", a.file_type)
        a.tags      = d.get("tags", {"Genre": [], "Mood": [], "Situation": [], "Mechanic": []})
        a.notes     = d.get("notes", "")
        return a
