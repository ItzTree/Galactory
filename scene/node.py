import os
from panda3d.core import (
    NodePath, CollisionNode, CollisionSphere, BitMask32, TextNode, LColor,
)
from core.config import (
    FOLDER_COLOR, FILE_COLORS, FILE_COLOR_DEFAULT, PERMISSION_ERROR_COLOR,
    FOLDER_SCALE, FILE_SCALE,
)
from core.filesystem import FileEntry
from scene.sphere_mesh import make_sphere, add_glow_card


def _file_color(name: str) -> tuple:
    ext = os.path.splitext(name)[1].lstrip(".").lower()
    return FILE_COLORS.get(ext, FILE_COLOR_DEFAULT)


def _brighten(color: tuple) -> tuple:
    """Blend color toward white by 40% for hover highlight."""
    return tuple(min(c + 0.4, 1.0) for c in color[:3]) + (color[3],)


def _to_core_color(color: tuple) -> tuple:
    """Blend color 65% toward white for the hot-core sphere appearance."""
    return (
        min(color[0] * 0.35 + 0.65, 1.0),
        min(color[1] * 0.35 + 0.65, 1.0),
        min(color[2] * 0.35 + 0.65, 1.0),
        color[3],
    )


# Bit mask used exclusively for mouse-picking collisions
PICK_MASK = BitMask32.bit(1)

_INNER_GLOW_COLOR = (1.0, 0.97, 0.9, 1.0)  # warm white for inner bloom


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
            color = _file_color(entry.name)

        scale = FOLDER_SCALE if self.is_dir else FILE_SCALE
        self._base_color = color

        # Root transform node
        self.root = parent_np.attachNewNode(f"xnode_{index}")

        # Sphere visual — near-white core (hot star appearance)
        model = make_sphere()
        model.setScale(scale)
        model.setColor(LColor(*_to_core_color(color)))
        model.setLightOff()
        model.reparentTo(self.root)
        self._model = model

        # Core hotspot: white disc covering whole sphere surface, depth test off
        # alpha gradient (center 1.0 → edge 0.0) gives bright white center, planet color at edges
        _core = add_glow_card(self.root, (1.0, 1.0, 1.0, 1.0), scale, intensity=0.85, radius_multiplier=1.0)
        _core.setDepthTest(False)
        _core.setBin("transparent", 20)  # render on top of all other glow layers
        # Inner bloom: warm white, tight — simulates overexposed core
        self._glow_inner = add_glow_card(self.root, _INNER_GLOW_COLOR, scale, intensity=1.0, radius_multiplier=1.1)
        # Outer halo: original color, moderate width — hollow_center prevents depth-precision dot
        self._glow_outer = add_glow_card(self.root, color, scale, intensity=0.65, radius_multiplier=2.0, hollow_center=True)

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
        base = _brighten(self._base_color) if hovered else self._base_color
        self._model.setColor(LColor(*_to_core_color(base)))
        self._glow_outer.setColorScale(*base[:3], 1.0)

    def cleanup(self) -> None:
        self.root.removeNode()