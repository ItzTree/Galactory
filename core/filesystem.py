import os
import threading
from dataclasses import dataclass
from typing import List, Callable


@dataclass
class FileEntry:
    name: str
    path: str
    is_dir: bool
    has_permission: bool = True


def scan_directory(path: str, callback: Callable[[List[FileEntry]], None]) -> None:
    """Scan `path` in a daemon thread; call `callback` with results on completion."""

    def _scan():
        entries: List[FileEntry] = []
        try:
            with os.scandir(path) as it:
                for entry in it:
                    try:
                        is_dir = entry.is_dir(follow_symlinks=False)
                        entries.append(FileEntry(
                            name=entry.name,
                            path=entry.path,
                            is_dir=is_dir,
                            has_permission=True,
                        ))
                    except PermissionError:
                        entries.append(FileEntry(
                            name=entry.name,
                            path=entry.path,
                            is_dir=False,
                            has_permission=False,
                        ))
        except PermissionError:
            pass

        # Directories first, then alphabetical
        entries.sort(key=lambda e: (not e.is_dir, e.name.lower()))
        callback(entries)

    threading.Thread(target=_scan, daemon=True).start()
