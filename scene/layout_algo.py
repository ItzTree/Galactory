import math
from typing import List, Tuple


def golden_sphere_positions(n: int, radius: float = 3.5) -> List[Tuple[float, float, float]]:
    """
    Distribute `n` points evenly on a sphere using the golden-angle Fibonacci spiral.
    Returns a list of (x, y, z) positions.
    Panda3D convention: Y is forward, Z is up.
    """
    if n == 0:
        return []
    if n == 1:
        return [(0.0, 0.0, radius)]

    golden_angle = math.pi * (3.0 - math.sqrt(5.0))  # ~137.508 degrees
    positions: List[Tuple[float, float, float]] = []

    for i in range(n):
        z_norm = 1.0 - (i / (n - 1)) * 2.0            # 1 → -1
        r_horiz = math.sqrt(max(0.0, 1.0 - z_norm ** 2))
        theta = golden_angle * i

        x = math.cos(theta) * r_horiz * radius
        y = math.sin(theta) * r_horiz * radius
        z = z_norm * radius

        positions.append((x, y, z))

    return positions
