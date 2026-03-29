from panda3d.core import (
    NodePath, CollisionNode, CollisionSphere, BitMask32, TextNode, LColor,
)
from core.config import (
    FOLDER_COLOR, FILE_COLOR, PERMISSION_ERROR_COLOR, HOVER_COLOR,
    FOLDER_SCALE, FILE_SCALE,
)
from core.filesystem import FileEntry

# Bit mask used exclusively for mouse-picking collisions
PICK_MASK = BitMask32.bit(1)


class ExplorerNode:
    def __init__(self, base, parent_np: NodePath, entry: FileEntry, index: int):
        self.base = base
        self.entry = entry
        self.name = entry.name
        self.path = entry.path
        self.is_dir = entry.is_dir
        self.has_permission = entry.has_permission

        if not self.has_permission:
            color = PERMISSION_ERROR_COLOR
        elif self.is_dir:
            color = FOLDER_COLOR
        else:
            color = FILE_COLOR

        scale = FOLDER_SCALE if self.is_dir else FILE_SCALE
        self._base_color = color

        # Root transform node
        self.root = parent_np.attachNewNode(f"xnode_{index}")

        # Sphere visual
        model = base.loader.loadModel("models/misc/sphere")
        model.setScale(scale)
        model.setColor(LColor(*color))
        model.reparentTo(self.root)
        self._model = model

        # Text label (billboarded, unlit)
        label_text = (self.name[:18] + "..") if len(self.name) > 20 else self.name
        tn = TextNode(f"lbl_{index}")
        tn.setFont(base.korean_font)
        tn.setText(label_text)
        tn.setAlign(TextNode.ACenter)
        tn.setShadow(0.06, 0.06)
        tn.setShadowColor(0, 0, 0, 1)
        tn.setTextColor(1, 1, 1, 1)
        lnp = self.root.attachNewNode(tn)
        lnp.setScale(0.075)
        lnp.setPos(0, 0, scale + 0.14)
        lnp.setBillboardPointEye()
        lnp.setLightOff()
        lnp.setDepthWrite(False)
        lnp.setBin("fixed", 50)

        # Collision sphere for picking (same radius as visual scale)
        cnode = CollisionNode(f"pick_{index}")
        cnode.addSolid(CollisionSphere(0, 0, 0, scale))
        cnode.setFromCollideMask(BitMask32.allOff())
        cnode.setIntoCollideMask(PICK_MASK)
        self.root.attachNewNode(cnode)

        # Back-reference so pick traversal can retrieve this object
        self.root.setPythonTag("xnode", self)

    def set_hover(self, hovered: bool) -> None:
        self._model.setColor(LColor(*(HOVER_COLOR if hovered else self._base_color)))

    def cleanup(self) -> None:
        self.root.removeNode()
