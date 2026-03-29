import math
from panda3d.core import MouseButton
from core.config import (
    CAMERA_DIST_DEFAULT, CAMERA_DIST_MIN, CAMERA_DIST_MAX,
    CAMERA_ZOOM_STEP, CAMERA_ROT_SPEED, CAMERA_DRAG_THRESHOLD,
)


class CameraController:
    def __init__(self, base):
        self.base = base
        self.dist = CAMERA_DIST_DEFAULT
        self.azimuth = 0.0     # horizontal angle, degrees
        self.elevation = 20.0  # vertical angle, degrees

        self._dragging = False
        self._moved = True      # start True so first frame is not treated as a click
        self._press_x = 0.0
        self._press_y = 0.0
        self._last_x = 0.0
        self._last_y = 0.0

        self._update_camera()

        base.accept("mouse1",     self._on_press)
        base.accept("mouse1-up",  self._on_release)
        base.accept("wheel_up",   self._zoom_in)
        base.accept("wheel_down", self._zoom_out)
        base.taskMgr.add(self._drag_task, "camera_drag")

    # ------------------------------------------------------------------
    def _update_camera(self) -> None:
        az = math.radians(self.azimuth)
        el = math.radians(self.elevation)
        x = self.dist * math.cos(el) * math.sin(az)
        y = -self.dist * math.cos(el) * math.cos(az)
        z = self.dist * math.sin(el)
        self.base.camera.setPos(x, y, z)
        self.base.camera.lookAt(0, 0, 0)

    def _on_press(self) -> None:
        if self.base.mouseWatcherNode.hasMouse():
            m = self.base.mouseWatcherNode.getMouse()
            self._press_x = self._last_x = m.x
            self._press_y = self._last_y = m.y
            self._dragging = True
            self._moved = False

    def _on_release(self) -> None:
        self._dragging = False

    def _zoom_in(self) -> None:
        self.dist = max(CAMERA_DIST_MIN, self.dist - CAMERA_ZOOM_STEP)
        self._update_camera()

    def _zoom_out(self) -> None:
        self.dist = min(CAMERA_DIST_MAX, self.dist + CAMERA_ZOOM_STEP)
        self._update_camera()

    def _drag_task(self, task):
        # 버튼 상태를 매 프레임 직접 확인 (mouse1-up 이벤트 누락 방지)
        btn_down = self.base.mouseWatcherNode.isButtonDown(MouseButton.one())
        if not btn_down:
            self._dragging = False

        if not self._dragging or not self.base.mouseWatcherNode.hasMouse():
            return task.cont

        m = self.base.mouseWatcherNode.getMouse()

        # Upgrade to drag once total movement exceeds threshold
        if (abs(m.x - self._press_x) > CAMERA_DRAG_THRESHOLD or
                abs(m.y - self._press_y) > CAMERA_DRAG_THRESHOLD):
            self._moved = True

        if self._moved:
            dx = m.x - self._last_x
            dy = m.y - self._last_y
            self.azimuth += dx * CAMERA_ROT_SPEED
            self.elevation = max(-80.0, min(80.0, self.elevation - dy * CAMERA_ROT_SPEED))
            self._update_camera()

        self._last_x = m.x
        self._last_y = m.y
        return task.cont

    # ------------------------------------------------------------------
    @property
    def was_click(self) -> bool:
        """True when mouse1 was released without a significant drag."""
        return not self._moved

    def reset(self) -> None:
        self.dist = CAMERA_DIST_DEFAULT
        self.azimuth = 0.0
        self.elevation = 20.0
        self._update_camera()
