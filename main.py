import sys
import tkinter as tk
from tkinter import filedialog

from panda3d.core import (
    load_prc_file_data, AmbientLight, DirectionalLight,
    LColor, AntialiasAttrib,
)
from direct.showbase.ShowBase import ShowBase

from core.config import WINDOW_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT, BG_COLOR
from scene.camera import CameraController
from scene.scene import FolderScene
from ui.hud import HUD


def pick_folder() -> str:
    """Show a native folder-picker dialog before Panda3D starts."""
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    folder = filedialog.askdirectory(title="탐색할 폴더를 선택하세요")
    root.destroy()
    return folder


def configure_panda3d() -> None:
    load_prc_file_data("", f"""
        window-title    {WINDOW_TITLE}
        win-size        {WINDOW_WIDTH} {WINDOW_HEIGHT}
        sync-video      0
        texture-anisotropic-degree 4
    """)


class App(ShowBase):
    def __init__(self, root_path: str):
        super().__init__()

        self.render.setAntialias(AntialiasAttrib.MAuto)
        self.setBackgroundColor(*BG_COLOR)
        self.disableMouse()  # camera managed manually

        # Lighting
        alight = AmbientLight("ambient")
        alight.setColor(LColor(0.25, 0.25, 0.30, 1))
        self.render.setLight(self.render.attachNewNode(alight))

        dlight = DirectionalLight("sun")
        dlight.setColor(LColor(0.85, 0.85, 0.80, 1))
        dlnp = self.render.attachNewNode(dlight)
        dlnp.setHpr(45, -45, 0)
        self.render.setLight(dlnp)

        # Korean font (Malgun Gothic bundled with Windows)
        self.korean_font = self.loader.loadFont("assets/fonts/NanumGothic.ttf")

        # Subsystems (order matters: hud + camera must exist before scene)
        self.camera_ctrl = CameraController(self)
        self.hud = HUD(self)
        self.folder_scene = FolderScene(self, root_path)

        self.accept("escape", self.folder_scene.go_back)


if __name__ == "__main__":
    folder = pick_folder()
    if not folder:
        sys.exit(0)

    configure_panda3d()
    app = App(folder)
    app.run()
