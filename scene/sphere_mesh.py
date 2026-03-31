import math
from panda3d.core import (
    GeomVertexFormat, GeomVertexData, GeomVertexWriter,
    GeomTriangles, Geom, GeomNode, NodePath,
)


def make_sphere(slices: int = 32, stacks: int = 16) -> NodePath:
    """Create a smooth UV sphere with radius 1, centered at origin.

    Returns a detached NodePath; call reparentTo() to attach it.
    slices/stacks controls polygon density (higher = smoother).
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