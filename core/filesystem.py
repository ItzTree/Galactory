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
    size: int = 0       # bytes (0 for dirs)
    mtime: float = 0.0  # Unix timestamp


def scan_directory(path: str, callback: Callable[[List[FileEntry]], None]) -> None:
    """Scan `path` in a daemon thread; call `callback` with results on completion."""

    def _scan():
        entries: List[FileEntry] = []
        try:
            with os.scandir(path) as it:
                for entry in it:
                    try:
                        is_dir = entry.is_dir(follow_symlinks=False)
                        try:
                            st = entry.stat(follow_symlinks=False)
                            size = 0 if is_dir else st.st_size
                            mtime = st.st_mtime
                        except OSError:
                            size, mtime = 0, 0.0
                        entries.append(FileEntry(
                            name=entry.name,
                            path=entry.path,
                            is_dir=is_dir,
                            has_permission=True,
                            size=size,
                            mtime=mtime,
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
