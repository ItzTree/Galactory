import datetime
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode


class HUD:
    def __init__(self, base):
        self.base = base

        font = base.korean_font

        # Current path (top-left)
        self._path_label = OnscreenText(
            text="",
            pos=(-1.70, 0.93),
            scale=0.055,
            fg=(1.0, 1.0, 1.0, 1.0),
            shadow=(0.0, 0.0, 0.0, 0.8),
            align=TextNode.ALeft,
            mayChange=True,
            font=font,
        )

        # Loading indicator (center)
        self._loading_label = OnscreenText(
            text="불러오는 중...",
            pos=(0.0, 0.0),
            scale=0.09,
            fg=(1.0, 0.85, 0.2, 1.0),
            shadow=(0.0, 0.0, 0.0, 0.8),
            align=TextNode.ACenter,
            mayChange=False,
            font=font,
        )
        self._loading_label.hide()

        # Empty folder notice (center)
        self._empty_label = OnscreenText(
            text="빈 폴더입니다",
            pos=(0.0, 0.0),
            scale=0.09,
            fg=(0.55, 0.55, 0.55, 1.0),
            shadow=(0.0, 0.0, 0.0, 0.8),
            align=TextNode.ACenter,
            mayChange=False,
            font=font,
        )
        self._empty_label.hide()

        # Hint bar (bottom-center, permanent)
        OnscreenText(
            text="[클릭] 폴더진입/파일열기   [ESC] 뒤로   [드래그] 회전·노드이동   [스크롤] 줌",
            pos=(0.0, -0.93),
            scale=0.050,
            fg=(0.65, 0.65, 0.65, 1.0),
            shadow=(0.0, 0.0, 0.0, 0.7),
            align=TextNode.ACenter,
            font=font,
        )

        # Tooltip (bottom-left, above hint bar)
        self._tooltip = OnscreenText(
            text="",
            pos=(-1.70, -0.82),
            scale=0.048,
            fg=(0.9, 0.9, 0.9, 1.0),
            shadow=(0.0, 0.0, 0.0, 0.8),
            align=TextNode.ALeft,
            mayChange=True,
            font=font,
        )
        self._tooltip.hide()

    # ------------------------------------------------------------------
    def set_path(self, path: str) -> None:
        display = path if len(path) <= 72 else "\u2026" + path[-70:]
        self._path_label.setText(display)

    def set_loading(self, loading: bool) -> None:
        (self._loading_label.show if loading else self._loading_label.hide)()

    def set_empty(self, empty: bool) -> None:
        (self._empty_label.show if empty else self._empty_label.hide)()

    def set_tooltip(self, entry) -> None:
        """Show tooltip for an ExplorerNode's FileEntry, or hide if entry is None."""
        if entry is None:
            self._tooltip.hide()
            return
        if entry.is_dir:
            type_str = "폴더"
        else:
            type_str = _fmt_size(entry.size)
        if entry.mtime:
            dt_str = datetime.datetime.fromtimestamp(entry.mtime).strftime("%Y-%m-%d %H:%M")
        else:
            dt_str = ""
        parts = [type_str]
        if dt_str:
            parts.append(dt_str)
        self._tooltip.setText("  ".join(parts))
        self._tooltip.show()


def _fmt_size(size: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.0f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"
