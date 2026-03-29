import json
import os

_CONFIG_PATH = os.path.join(os.environ.get("APPDATA", ""), "3DExplorer", "config.json")


def _load() -> dict:
    try:
        with open(_CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(data: dict) -> None:
    try:
        os.makedirs(os.path.dirname(_CONFIG_PATH), exist_ok=True)
        with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def get_last_path() -> str:
    path = _load().get("last_path", "")
    return path if os.path.isdir(path) else ""


def get_nav_stack() -> list:
    """Return saved history stack, filtering out paths that no longer exist."""
    stack = _load().get("nav_stack", [])
    return [p for p in stack if os.path.isdir(p)]


def set_nav_state(path: str, stack: list) -> None:
    data = _load()
    data["last_path"] = path
    data["nav_stack"] = stack
    _save(data)