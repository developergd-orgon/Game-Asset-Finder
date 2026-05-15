"""
Library — scans folders, persists metadata to JSON, handles rename/move.
"""
import json
import shutil
from pathlib import Path
from typing import Callable, Optional

from models.asset import Asset, ext_to_group, FILE_TYPES

DB_FILE = Path.home() / ".asset-finder" / "library.json"


class Library:
    def __init__(self):
        self._assets: dict[str, Asset] = {}   # str(path) → Asset
        self._load()

    # ── Persistence ──────────────────────────────────────────────────────────
    def _load(self):
        if DB_FILE.exists():
            try:
                raw = json.loads(DB_FILE.read_text(encoding="utf-8"))
                for d in raw:
                    try:
                        a = Asset.from_dict(d)
                        if a.path.exists():
                            self._assets[str(a.path)] = a
                    except Exception:
                        pass
            except Exception:
                pass

    def save(self):
        DB_FILE.parent.mkdir(parents=True, exist_ok=True)
        DB_FILE.write_text(
            json.dumps([a.to_dict() for a in self._assets.values()], indent=2),
            encoding="utf-8",
        )

    # ── Scanning ─────────────────────────────────────────────────────────────
    def scan_folder(
        self,
        folder: Path,
        recursive: bool = True,
        progress_cb: Optional[Callable[[int, str], None]] = None,
    ) -> int:
        """Walk *folder*, add new files, return count of NEW files added."""
        all_exts = set()
        for exts in FILE_TYPES.values():
            all_exts |= exts

        found = list(folder.rglob("*") if recursive else folder.glob("*"))
        new = 0
        for i, p in enumerate(found):
            if not p.is_file():
                continue
            if p.suffix.lower() not in all_exts:
                continue
            key = str(p)
            if key not in self._assets:
                self._assets[key] = Asset(path=p)
                new += 1
            if progress_cb:
                progress_cb(i + 1, p.name)
        self.save()
        return new

    # ── CRUD helpers ──────────────────────────────────────────────────────────
    def all_assets(self) -> list[Asset]:
        return list(self._assets.values())

    def get(self, path: Path) -> Optional[Asset]:
        return self._assets.get(str(path))

    def update(self, asset: Asset):
        self._assets[str(asset.path)] = asset
        self.save()

    def remove(self, asset: Asset):
        self._assets.pop(str(asset.path), None)
        self.save()

    def rename_file(self, asset: Asset, new_stem: str) -> Asset:
        """Rename the file on disk and update the library entry."""
        old_path = asset.path
        new_path = old_path.with_name(new_stem + old_path.suffix)
        if new_path.exists():
            raise FileExistsError(f"'{new_path.name}' already exists in that folder.")
        old_path.rename(new_path)
        self._assets.pop(str(old_path), None)
        asset.path = new_path
        asset.name = new_stem
        self._assets[str(new_path)] = asset
        self.save()
        return asset

    def move_file(self, asset: Asset, dest_folder: Path) -> Asset:
        """Move the file to *dest_folder* and update the library entry."""
        old_path = asset.path
        new_path = dest_folder / old_path.name
        if new_path.exists():
            raise FileExistsError(f"A file named '{old_path.name}' already exists in the destination.")
        dest_folder.mkdir(parents=True, exist_ok=True)
        shutil.move(str(old_path), new_path)
        self._assets.pop(str(old_path), None)
        asset.path = new_path
        self._assets[str(new_path)] = asset
        self.save()
        return asset

    def toggle_ignore(self, asset: Asset) -> None:
        asset.ignored = not asset.ignored
        self.update(asset)  # persiste automáticamente

    # ── Filtering ─────────────────────────────────────────────────────────────
    def filter(
        self,
        text: str = "",
        file_type: str = "All",
        tags: Optional[list[str]] = None,
        show_ignored: bool = False,
    ) -> list[Asset]:
        results = list(self._assets.values())

        if not show_ignored:
            results = [a for a in results if not a.ignored]

        if file_type and file_type != "All":
            results = [a for a in results if a.file_type == file_type]

        if text:
            lo = text.lower()
            results = [
                a for a in results
                if lo in a.name.lower()
                or lo in str(a.path).lower()
                or any(lo in t.lower() for t in a.all_tags())
            ]

        if tags:
            results = [
                a for a in results
                if all(t in a.all_tags() for t in tags)
            ]

        return results

