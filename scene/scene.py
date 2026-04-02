import math
import os
import time
from typing import List, Optional

from panda3d.core import (
    CollisionTraverser, CollisionRay, CollisionNode,
    CollisionHandlerQueue, BitMask32, NodePath,
    LColor, TextNode, Point3,
)

from core.filesystem import FileEntry, scan_directory
from core.config import SPHERE_RADIUS, MAX_NODES, CENTER_PLANET_SCALE, CENTER_PLANET_COLOR, CAMERA_DRAG_THRESHOLD
from core.app_config import get_nav_stack, set_nav_state, load_layout, save_layout
from scene.layout_algo import golden_sphere_positions
from scene.node import ExplorerNode, PICK_MASK
from scene.sphere_mesh import make_sphere

_DOUBLE_CLICK_INTERVAL = 0.35  # seconds


class FolderScene:
    def __init__(self, base, root_path: str):
        self.base = base
        self._history: List[str] = []
        self._current_path: str = ""
        self._nodes: List[ExplorerNode] = []

        # Scene root — all 3D nodes live here
        self._root = base.render.attachNewNode("scene_root")

        # Collision picker
        self._picker = CollisionTraverser("picker")
        self._pick_handler = CollisionHandlerQueue()
        self._pick_ray = CollisionRay()
        pick_cnode = CollisionNode("mouse_ray")
        pick_cnode.addSolid(self._pick_ray)
        pick_cnode.setFromCollideMask(PICK_MASK)
        pick_cnode.setIntoCollideMask(BitMask32.allOff())
        self._pick_ray_np = base.camera.attachNewNode(pick_cnode)
        self._picker.addCollider(self._pick_ray_np, self._pick_handler)

        # Center planet
        self._center_planet: Optional[NodePath] = None

        # Hover state
        self._hovered: Optional[ExplorerNode] = None
        base.taskMgr.add(self._hover_task, "hover_task")

        # Node drag state
        self._dragging_node: Optional[ExplorerNode] = None
        base.node_drag_active = False
        self._node_press_x: float = 0.0
        self._node_press_y: float = 0.0
        self._node_is_drag: bool = False
        base.accept("mouse1",    self._on_mouse_press)
        base.accept("mouse1-up", self._on_mouse_release)
        base.taskMgr.add(self._node_drag_task, "node_drag_task")

        # Double-click tracking
        self._last_click_node: Optional[ExplorerNode] = None
        self._last_click_time: float = 0.0

        self._history = get_nav_stack()
        self._navigate_to(root_path)

    # ------------------------------------------------------------------
    def _navigate_to(self, path: str) -> None:
        self._clear_nodes()
        self._current_path = path
        set_nav_state(path, self._history)
        self.base.hud.set_path(path)
        self.base.hud.set_loading(True)
        scan_directory(path, self._on_scan_done)

    def _on_scan_done(self, entries: List[FileEntry]) -> None:
        """Called from background thread — marshal to main thread."""
        def _task(task, e=entries):
            self._build_scene(e)
            return task.done
        self.base.taskMgr.doMethodLater(0, _task, "build_scene")

    def _build_scene(self, entries: List[FileEntry]) -> None:
        self.base.hud.set_loading(False)
        self._build_center_planet()

        if not entries:
            self.base.hud.set_empty(True)
            return

        self.base.hud.set_empty(False)
        visible = entries[:MAX_NODES]
        default_positions = golden_sphere_positions(len(visible), SPHERE_RADIUS)
        saved = load_layout(self._current_path)

        for i, (entry, default_pos) in enumerate(zip(visible, default_positions)):
            node = ExplorerNode(self.base, self._root, entry, i)
            if entry.name in saved:
                node.root.setPos(*saved[entry.name])
            else:
                node.root.setPos(*default_pos)
            self._nodes.append(node)

    def _build_center_planet(self) -> None:
        folder_name = self._current_path.split("/")[-1] or self._current_path.split("\\")[-1] or self._current_path

        np = self._root.attachNewNode("center_planet")

        model = make_sphere()
        model.setScale(CENTER_PLANET_SCALE)
        model.setColor(LColor(*CENTER_PLANET_COLOR))
        model.setLightOff()
        model.reparentTo(np)


        label_text = (folder_name[:18] + "..") if len(folder_name) > 20 else folder_name
        tn = TextNode("center_lbl")
        tn.setFont(self.base.korean_font)
        tn.setText(label_text)
        tn.setAlign(TextNode.ACenter)
        tn.setShadow(0.06, 0.06)
        tn.setShadowColor(0, 0, 0, 1)
        tn.setTextColor(1, 1, 1, 1)
        lnp = np.attachNewNode(tn)
        lnp.setScale(0.075)
        lnp.setPos(0, 0, CENTER_PLANET_SCALE + 0.14)
        lnp.setBillboardPointEye()
        lnp.setLightOff()
        lnp.setDepthWrite(False)
        lnp.setBin("fixed", 50)

        self._center_planet = np

    def _clear_nodes(self) -> None:
        self._hovered = None
        for n in self._nodes:
            n.cleanup()
        self._nodes.clear()
        if self._center_planet:
            self._center_planet.removeNode()
            self._center_planet = None
        self.base.hud.set_empty(False)

    # ------------------------------------------------------------------
    def _pick_at_mouse(self) -> Optional[ExplorerNode]:
        """Run collision pick at current mouse position; return hit ExplorerNode or None."""
        if not self.base.mouseWatcherNode.hasMouse():
            return None
        mpos = self.base.mouseWatcherNode.getMouse()
        self._pick_ray.setFromLens(self.base.camNode, mpos.x, mpos.y)
        self._picker.traverse(self._root)
        if self._pick_handler.getNumEntries() == 0:
            return None
        self._pick_handler.sortEntries()
        hit_np: NodePath = self._pick_handler.getEntry(0).getIntoNodePath()
        # Walk up the node tree to find the ExplorerNode tag
        np = hit_np
        while np and not np.isEmpty():
            xnode = np.getPythonTag("xnode")
            if xnode is not None:
                return xnode
            np = np.getParent()
        return None

    def _hover_task(self, task):
        new_hovered = self._pick_at_mouse()
        if new_hovered is not self._hovered:
            if self._hovered:
                self._hovered.set_hover(False)
            if new_hovered:
                new_hovered.set_hover(True)
            self._hovered = new_hovered
            self.base.hud.set_tooltip(new_hovered.entry if new_hovered else None)
        return task.cont

    # ------------------------------------------------------------------
    # Node drag
    # ------------------------------------------------------------------
    def _on_mouse_press(self) -> None:
        xnode = self._pick_at_mouse()
        if xnode is None:
            # 빈 배경 클릭 → 카메라 드래그로 위임
            self.base.camera_ctrl._on_press()
            return
        self._dragging_node = xnode
        self._node_is_drag = False
        if self.base.mouseWatcherNode.hasMouse():
            m = self.base.mouseWatcherNode.getMouse()
            self._node_press_x = m.x
            self._node_press_y = m.y
        self.base.node_drag_active = True

    def _on_mouse_release(self) -> None:
        had_node = self.base.node_drag_active
        was_node_drag = had_node and self._node_is_drag
        was_node_click = had_node and not self._node_is_drag

        if was_node_drag:
            self._save_current_layout()
        self._dragging_node = None
        self.base.node_drag_active = False

        # Trigger click when: node was pressed without drag, OR no node was involved and camera says click
        if was_node_click or (not had_node and self.base.camera_ctrl.was_click):
            self._handle_click()

    def _node_drag_task(self, task):
        if not self.base.node_drag_active or self._dragging_node is None:
            return task.cont
        if not self.base.mouseWatcherNode.hasMouse():
            return task.cont

        m = self.base.mouseWatcherNode.getMouse()
        if not self._node_is_drag:
            if (abs(m.x - self._node_press_x) > CAMERA_DRAG_THRESHOLD or
                    abs(m.y - self._node_press_y) > CAMERA_DRAG_THRESHOLD):
                self._node_is_drag = True

        if self._node_is_drag:
            pos = self._mouse_to_sphere(SPHERE_RADIUS)
            if pos is not None:
                self._dragging_node.root.setPos(*pos)
        return task.cont

    def _mouse_to_sphere(self, radius: float):
        """Cast ray from camera through mouse; return intersection with sphere of given radius."""
        mpos = self.base.mouseWatcherNode.getMouse()
        near = Point3()
        far = Point3()
        self.base.camLens.extrude(mpos, near, far)
        near_w = self.base.render.getRelativePoint(self.base.camera, near)
        far_w = self.base.render.getRelativePoint(self.base.camera, far)
        dx = far_w.x - near_w.x
        dy = far_w.y - near_w.y
        dz = far_w.z - near_w.z
        length = math.sqrt(dx*dx + dy*dy + dz*dz)
        if length == 0:
            return None
        dx /= length; dy /= length; dz /= length
        ox, oy, oz = near_w.x, near_w.y, near_w.z
        b = ox*dx + oy*dy + oz*dz
        c = ox*ox + oy*oy + oz*oz - radius*radius
        disc = b*b - c
        if disc < 0:
            return None
        t = -b - math.sqrt(disc)
        if t < 0:
            t = -b + math.sqrt(disc)
        if t < 0:
            return None
        return (ox + t*dx, oy + t*dy, oz + t*dz)

    def _save_current_layout(self) -> None:
        positions = {n.name: list(n.root.getPos()) for n in self._nodes}
        save_layout(self._current_path, positions)

    # ------------------------------------------------------------------
    # Click / double-click
    # ------------------------------------------------------------------
    def _handle_click(self) -> None:
        xnode = self._pick_at_mouse()
        now = time.monotonic()

        is_double = (
            xnode is not None
            and xnode is self._last_click_node
            and (now - self._last_click_time) < _DOUBLE_CLICK_INTERVAL
        )

        self._last_click_node = xnode
        self._last_click_time = now

        if xnode is None or not xnode.has_permission:
            return

        if is_double:
            # Double-click: open file (folders are handled by first click)
            if not xnode.is_dir:
                try:
                    os.startfile(xnode.path)
                except Exception:
                    pass
        else:
            # Single click: enter folder
            if xnode.is_dir:
                self._history.append(self._current_path)
                self.base.camera_ctrl.reset()
                self._navigate_to(xnode.path)

    # ------------------------------------------------------------------
    def go_back(self) -> None:
        if self._history:
            self.base.camera_ctrl.reset()
            self._navigate_to(self._history.pop())
