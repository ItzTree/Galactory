from typing import List, Optional

from panda3d.core import (
    CollisionTraverser, CollisionRay, CollisionNode,
    CollisionHandlerQueue, BitMask32, NodePath,
    TransparencyAttrib, LColor, TextNode,
)

from core.filesystem import FileEntry, scan_directory
from core.config import SPHERE_RADIUS, MAX_NODES, CENTER_PLANET_SCALE, CENTER_PLANET_COLOR
from core.app_config import get_nav_stack, set_nav_state
from scene.layout_algo import golden_sphere_positions
from scene.node import ExplorerNode, PICK_MASK


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

        # Click handler
        base.accept("mouse1-up", self._on_click)

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
        positions = golden_sphere_positions(len(visible), SPHERE_RADIUS)

        for i, (entry, pos) in enumerate(zip(visible, positions)):
            node = ExplorerNode(self.base, self._root, entry, i)
            node.root.setPos(*pos)
            self._nodes.append(node)

    def _build_center_planet(self) -> None:
        folder_name = self._current_path.split("/")[-1] or self._current_path.split("\\")[-1] or self._current_path

        np = self._root.attachNewNode("center_planet")

        model = self.base.loader.loadModel("models/misc/sphere")
        model.setScale(CENTER_PLANET_SCALE)
        model.setColor(LColor(*CENTER_PLANET_COLOR))
        model.setTransparency(TransparencyAttrib.MAlpha)
        model.setDepthWrite(False)
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
        return task.cont

    def _on_click(self) -> None:
        if not self.base.camera_ctrl.was_click:
            return
        xnode = self._pick_at_mouse()
        if xnode and xnode.is_dir and xnode.has_permission:
            self._history.append(self._current_path)
            self.base.camera_ctrl.reset()
            self._navigate_to(xnode.path)

    # ------------------------------------------------------------------
    def go_back(self) -> None:
        if self._history:
            self.base.camera_ctrl.reset()
            self._navigate_to(self._history.pop())
