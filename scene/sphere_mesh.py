import math
from panda3d.core import (
    GeomVertexFormat, GeomVertexData, GeomVertexWriter,
    GeomTriangles, Geom, GeomNode, NodePath,
    ColorBlendAttrib, TransparencyAttrib,
)

# Two cached glow Geoms:
#   _GLOW_DISC — bright center (alpha 1.0 at center), for core hotspot / inner bloom
#   _GLOW_RING — zero-alpha center, for outer halo (prevents colored dot at sphere center)
_GLOW_DISC: Geom | None = None
_GLOW_RING: Geom | None = None


def _build_glow_geom(segments: int = 48, center_alpha: float = 1.0) -> Geom:
    """Flat disc in the XZ plane with radial vertex-color alpha gradient.

    center_alpha=1.0 → bright disc (core hotspot / inner bloom)
    center_alpha=0.0 → hollow ring (outer halo — prevents depth-precision dot at sphere center)
    """
    rings = [
        (0.00, center_alpha),
        (0.10, 0.85),
        (0.25, 0.65),
        (0.45, 0.40),
        (0.65, 0.18),
        (0.85, 0.05),
        (1.00, 0.00),
    ]

    fmt = GeomVertexFormat.getV3c4()
    vdata = GeomVertexData("glow_disc", fmt, Geom.UHStatic)
    vw = GeomVertexWriter(vdata, "vertex")
    cw = GeomVertexWriter(vdata, "color")

    # Vertex 0: center
    vw.addData3(0, 0, 0)
    cw.addData4(1, 1, 1, rings[0][1])

    # Ring vertices (in XZ plane, Y=0 so +Y normal faces camera via billboard)
    for radius, alpha in rings[1:]:
        for i in range(segments):
            theta = 2.0 * math.pi * i / segments
            vw.addData3(radius * math.cos(theta), 0, radius * math.sin(theta))
            cw.addData4(1, 1, 1, alpha)

    tris = GeomTriangles(Geom.UHStatic)

    # Fan: center → first ring  (winding: center, v2, v1 → +Y normal)
    for i in range(segments):
        v1 = 1 + i
        v2 = 1 + (i + 1) % segments
        tris.addVertices(0, v2, v1)

    # Quads between consecutive rings
    for ring_idx in range(len(rings) - 2):
        curr = 1 + ring_idx * segments
        nxt  = curr + segments
        for i in range(segments):
            v0 = curr + i
            v1 = curr + (i + 1) % segments
            v2 = nxt  + i
            v3 = nxt  + (i + 1) % segments
            tris.addVertices(v0, v2, v1)   # +Y normal
            tris.addVertices(v1, v2, v3)   # +Y normal

    geom = Geom(vdata)
    geom.addPrimitive(tris)
    return geom


def _get_glow_disc() -> Geom:
    global _GLOW_DISC
    if _GLOW_DISC is None:
        _GLOW_DISC = _build_glow_geom(center_alpha=1.0)
    return _GLOW_DISC


def _get_glow_ring() -> Geom:
    global _GLOW_RING
    if _GLOW_RING is None:
        _GLOW_RING = _build_glow_geom(center_alpha=0.0)
    return _GLOW_RING


# ---------------------------------------------------------------------------

def make_sphere(slices: int = 32, stacks: int = 16) -> NodePath:
    """Create a smooth UV sphere with radius 1, centered at origin.

    Returns a detached NodePath; call reparentTo() to attach it.
    """
    fmt = GeomVertexFormat.getV3n3()
    vdata = GeomVertexData("sphere", fmt, Geom.UHStatic)
    vertex = GeomVertexWriter(vdata, "vertex")
    normal = GeomVertexWriter(vdata, "normal")

    for j in range(stacks + 1):
        phi = math.pi * j / stacks
        sin_phi = math.sin(phi)
        cos_phi = math.cos(phi)
        for i in range(slices + 1):
            theta = 2.0 * math.pi * i / slices
            x = sin_phi * math.cos(theta)
            y = sin_phi * math.sin(theta)
            z = cos_phi
            vertex.addData3(x, y, z)
            normal.addData3(x, y, z)

    tris = GeomTriangles(Geom.UHStatic)
    for j in range(stacks):
        for i in range(slices):
            v0 = j * (slices + 1) + i
            v1 = v0 + 1
            v2 = v0 + (slices + 1)
            v3 = v2 + 1
            tris.addVertices(v0, v2, v1)
            tris.addVertices(v1, v2, v3)

    geom = Geom(vdata)
    geom.addPrimitive(tris)
    node = GeomNode("sphere_geom")
    node.addGeom(geom)
    return NodePath(node)


def add_glow_card(
    parent_np: NodePath,
    color: tuple,
    sphere_scale: float,
    intensity: float = 1.0,
    radius_multiplier: float = 3.0,
    hollow_center: bool = False,
) -> NodePath:
    """Attach an additive-blended billboard glow halo to *parent_np*.

    color             — (R, G, B, ...) of the sphere; the halo is tinted to match.
    sphere_scale      — visual scale of the sphere model (e.g. FOLDER_SCALE).
    intensity         — overall glow brightness, 0.0 (none) … 1.0 (full).
                        Scales all vertex alphas via setColorScale.
    radius_multiplier — how many times larger than sphere_scale the halo extends.
                        1.5~2.0 for tight glow, 3.0+ for wide nebula-style halo.
    hollow_center     — if True, uses a ring geometry (center alpha=0) instead of
                        a disc (center alpha=1). Use for outer halo to prevent a
                        depth-precision colored dot at the sphere center.
    Returns the glow NodePath (already parented and configured).
    """
    geom = _get_glow_ring() if hollow_center else _get_glow_disc()
    node = GeomNode("glow_disc")
    node.addGeom(geom)
    glow = parent_np.attachNewNode(node)

    # Tint to sphere color; intensity scales vertex alphas (preserves gradient shape)
    r, g, b = color[0], color[1], color[2]
    glow.setColorScale(r, g, b, max(0.0, min(1.0, intensity)))

    # Halo world-space radius = sphere_scale * radius_multiplier
    glow.setScale(sphere_scale * radius_multiplier)

    # Full billboard: local Y axis always points toward camera eye
    glow.setBillboardPointEye()

    # Additive blending: output = src_color * src_alpha + existing_color
    # This makes the glow brighten whatever is behind it (like real light).
    glow.setTransparency(TransparencyAttrib.MAlpha)
    glow.setAttrib(ColorBlendAttrib.make(
        ColorBlendAttrib.MAdd,
        ColorBlendAttrib.OIncomingAlpha,
        ColorBlendAttrib.OOne,
    ))
    glow.setDepthWrite(False)
    glow.setBin("transparent", 5)
    glow.setLightOff()

    return glow