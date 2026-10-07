"""Stock material models (Dexel and Octree) for Ap/Ae calculation."""

from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


class MaterialRepresentation(Enum):
    """Types of stock material representations."""

    DEXEL = "dexel"  # Z-height map per XY column
    OCTREE = "octree"  # Octree spatial partitioning
    VOXEL = "voxel"  # Simple voxel grid


@dataclass
class Point3D:
    """3D point representation."""

    x: float
    y: float
    z: float

    def to_tuple(self) -> Tuple[float, float, float]:
        """Convert to tuple."""
        return (self.x, self.y, self.z)

    def distance_to(self, other: "Point3D") -> float:
        """Calculate distance to another point."""
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2 + (self.z - other.z) ** 2) ** 0.5


@dataclass
class Material:
    """Material properties."""

    density: float = 2.7  # g/cm³ (Aluminum)
    hardness: float = 95  # HV (Vickers hardness)
    thermal_conductivity: float = 205  # W/(m·K)
    machinability: float = 8.0  # Machinability index (8.0 = Aluminum 6061)
    name: str = "Aluminum 6061"


class DexelModel:
    """
    Dexel (Depth cell) model for stock representation.

    Each XY grid point stores a list of z-intervals occupied by material.
    Efficient for 2.5D machining operations.
    """

    def __init__(
        self,
        x_min: float,
        x_max: float,
        y_min: float,
        y_max: float,
        z_min: float,
        z_max: float,
        resolution: float = 1.0,
        material: Optional[Material] = None,
    ):
        """Initialize Dexel model.

        Args:
            x_min, x_max: X bounds
            y_min, y_max: Y bounds
            z_min, z_max: Z bounds
            resolution: Grid resolution (mm)
            material: Material properties
        """
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max
        self.z_min = z_min
        self.z_max = z_max
        self.resolution = resolution
        self.material = material or Material()

        # Calculate grid dimensions
        self.nx = int((x_max - x_min) / resolution) + 1
        self.ny = int((y_max - y_min) / resolution) + 1

        # Grid of depth segments (dexels)
        # Each dexel is a list of (z_bottom, z_top) tuples representing material
        self.dexels: Dict[Tuple[int, int], List[Tuple[float, float]]] = {}

        # Initialize with full stock
        self._initialize_stock()

    def _initialize_stock(self):
        """Initialize stock with full material from z_min to z_max."""
        for i in range(self.nx):
            for j in range(self.ny):
                self.dexels[(i, j)] = [(self.z_min, self.z_max)]

    def get_xy_position(self, i: int, j: int) -> Tuple[float, float]:
        """Get XY coordinates for grid indices."""
        x = self.x_min + i * self.resolution
        y = self.y_min + j * self.resolution
        return (x, y)

    def get_material_height(self, x: float, y: float) -> float:
        """Get top surface height at XY position.

        Args:
            x, y: Position coordinates

        Returns:
            Maximum z value (top of material)
        """
        i = int((x - self.x_min) / self.resolution)
        j = int((y - self.y_min) / self.resolution)

        # Clamp to grid bounds
        i = max(0, min(i, self.nx - 1))
        j = max(0, min(j, self.ny - 1))

        dexel = self.dexels.get((i, j), [])
        if not dexel:
            return self.z_min

        # Return top of highest segment
        return max(seg[1] for seg in dexel)

    def remove_material_box(
        self,
        x1: float,
        x2: float,
        y1: float,
        y2: float,
        z1: float,
        z2: float,
    ):
        """Remove material in a box region.

        Args:
            x1, x2: X bounds (min, max)
            y1, y2: Y bounds (min, max)
            z1, z2: Z bounds (min, max)
        """
        i_min = int((x1 - self.x_min) / self.resolution)
        i_max = int((x2 - self.x_min) / self.resolution) + 1
        j_min = int((y1 - self.y_min) / self.resolution)
        j_max = int((y2 - self.y_min) / self.resolution) + 1

        for i in range(max(0, i_min), min(self.nx, i_max)):
            for j in range(max(0, j_min), min(self.ny, j_max)):
                self._remove_material_dexel(i, j, z1, z2)

    def _remove_material_dexel(self, i: int, j: int, z1: float, z2: float):
        """Remove material from a single dexel."""
        key = (i, j)
        if key not in self.dexels:
            return

        old_segments = self.dexels[key]
        new_segments = []

        for z_bottom, z_top in old_segments:
            # Case 1: Removal zone doesn't overlap
            if z_top <= z1 or z_bottom >= z2:
                new_segments.append((z_bottom, z_top))
            # Case 2: Removal zone completely covers segment
            elif z1 <= z_bottom and z2 >= z_top:
                continue  # Remove entire segment
            # Case 3: Partial overlap - split segment
            else:
                if z_bottom < z1:
                    new_segments.append((z_bottom, z1))
                if z_top > z2:
                    new_segments.append((z2, z_top))

        self.dexels[key] = new_segments

    def get_material_volume(self) -> float:
        """Calculate total material volume.

        Returns:
            Volume in mm³
        """
        volume = 0.0
        cell_area = self.resolution**2
        for dexel in self.dexels.values():
            for z_bottom, z_top in dexel:
                volume += (z_top - z_bottom) * cell_area
        return volume

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "type": "dexel",
            "bounds": {
                "x": [self.x_min, self.x_max],
                "y": [self.y_min, self.y_max],
                "z": [self.z_min, self.z_max],
            },
            "resolution": self.resolution,
            "grid_size": [self.nx, self.ny],
            "total_dexels": len(self.dexels),
            "material": {
                "name": self.material.name,
                "density": self.material.density,
            },
        }


class OctreeNode:
    """Node in an Octree structure."""

    def __init__(
        self,
        x_min: float,
        x_max: float,
        y_min: float,
        y_max: float,
        z_min: float,
        z_max: float,
        depth: int = 0,
        max_depth: int = 8,
    ):
        """Initialize octree node.

        Args:
            x_min, x_max: X bounds
            y_min, y_max: Y bounds
            z_min, z_max: Z bounds
            depth: Current depth in tree
            max_depth: Maximum tree depth
        """
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max
        self.z_min = z_min
        self.z_max = z_max
        self.depth = depth
        self.max_depth = max_depth

        self.children: Optional[List[OctreeNode]] = None
        self.is_full = True  # Initially all material
        self.is_empty = False

    def subdivide(self):
        """Subdivide into 8 octants."""
        if self.depth >= self.max_depth:
            return

        x_mid = (self.x_min + self.x_max) / 2
        y_mid = (self.y_min + self.y_max) / 2
        z_mid = (self.z_min + self.z_max) / 2

        self.children = [
            OctreeNode(
                self.x_min,
                x_mid,
                self.y_min,
                y_mid,
                self.z_min,
                z_mid,
                self.depth + 1,
                self.max_depth,
            ),
            OctreeNode(
                x_mid,
                self.x_max,
                self.y_min,
                y_mid,
                self.z_min,
                z_mid,
                self.depth + 1,
                self.max_depth,
            ),
            OctreeNode(
                self.x_min,
                x_mid,
                y_mid,
                self.y_max,
                self.z_min,
                z_mid,
                self.depth + 1,
                self.max_depth,
            ),
            OctreeNode(
                x_mid,
                self.x_max,
                y_mid,
                self.y_max,
                self.z_min,
                z_mid,
                self.depth + 1,
                self.max_depth,
            ),
            OctreeNode(
                self.x_min,
                x_mid,
                self.y_min,
                y_mid,
                z_mid,
                self.z_max,
                self.depth + 1,
                self.max_depth,
            ),
            OctreeNode(
                x_mid,
                self.x_max,
                self.y_min,
                y_mid,
                z_mid,
                self.z_max,
                self.depth + 1,
                self.max_depth,
            ),
            OctreeNode(
                self.x_min,
                x_mid,
                y_mid,
                self.y_max,
                z_mid,
                self.z_max,
                self.depth + 1,
                self.max_depth,
            ),
            OctreeNode(
                x_mid,
                self.x_max,
                y_mid,
                self.y_max,
                z_mid,
                self.z_max,
                self.depth + 1,
                self.max_depth,
            ),
        ]

    def get_volume(self) -> float:
        """Calculate node volume."""
        dx = self.x_max - self.x_min
        dy = self.y_max - self.y_min
        dz = self.z_max - self.z_min
        return dx * dy * dz


class OctreeModel:
    """
    Octree-based stock representation.

    Provides hierarchical spatial partitioning for efficient
    material volume calculations and intersection queries.
    """

    def __init__(
        self,
        x_min: float,
        x_max: float,
        y_min: float,
        y_max: float,
        z_min: float,
        z_max: float,
        max_depth: int = 8,
        material: Optional[Material] = None,
    ):
        """Initialize Octree model.

        Args:
            x_min, x_max: X bounds
            y_min, y_max: Y bounds
            z_min, z_max: Z bounds
            max_depth: Maximum tree depth
            material: Material properties
        """
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max
        self.z_min = z_min
        self.z_max = z_max
        self.max_depth = max_depth
        self.material = material or Material()

        # Root node
        self.root = OctreeNode(x_min, x_max, y_min, y_max, z_min, z_max, 0, max_depth)

    def remove_material_sphere(
        self,
        cx: float,
        cy: float,
        cz: float,
        radius: float,
        tolerance: float = 0.1,
    ) -> int:
        """Remove material in a spherical region.

        Args:
            cx, cy, cz: Sphere center
            radius: Sphere radius
            tolerance: Tolerance for sphere inclusion

        Returns:
            Number of nodes cleared
        """
        count = 0
        self._remove_sphere_recursive(self.root, cx, cy, cz, radius, tolerance)
        return count

    def _remove_sphere_recursive(
        self,
        node: OctreeNode,
        cx: float,
        cy: float,
        cz: float,
        radius: float,
        tolerance: float,
    ) -> int:
        """Recursively remove material from octree."""
        # Check if sphere intersects node
        dist = self._distance_point_to_box(
            cx,
            cy,
            cz,
            node.x_min,
            node.x_max,
            node.y_min,
            node.y_max,
            node.z_min,
            node.z_max,
        )

        if dist > radius + tolerance:
            return 0  # No intersection

        # Check if sphere completely contains node
        if self._point_in_sphere(
            (node.x_min + node.x_max) / 2,
            (node.y_min + node.y_max) / 2,
            (node.z_min + node.z_max) / 2,
            cx,
            cy,
            cz,
            radius,
        ) and self._box_in_sphere(
            node.x_min,
            node.x_max,
            node.y_min,
            node.y_max,
            node.z_min,
            node.z_max,
            cx,
            cy,
            cz,
            radius,
        ):
            node.is_full = False
            node.is_empty = True
            node.children = None
            return 1

        # Partial intersection - subdivide
        if node.children is None:
            node.subdivide()

        count = 0
        if node.children:
            for child in node.children:
                count += self._remove_sphere_recursive(child, cx, cy, cz, radius, tolerance)

        return count

    @staticmethod
    def _distance_point_to_box(
        px: float,
        py: float,
        pz: float,
        x1: float,
        x2: float,
        y1: float,
        y2: float,
        z1: float,
        z2: float,
    ) -> float:
        """Calculate minimum distance from point to box."""
        dx = max(x1 - px, 0, px - x2)
        dy = max(y1 - py, 0, py - y2)
        dz = max(z1 - pz, 0, pz - z2)
        return (dx**2 + dy**2 + dz**2) ** 0.5

    @staticmethod
    def _point_in_sphere(
        px: float,
        py: float,
        pz: float,
        cx: float,
        cy: float,
        cz: float,
        radius: float,
    ) -> bool:
        """Check if point is in sphere."""
        dist = ((px - cx) ** 2 + (py - cy) ** 2 + (pz - cz) ** 2) ** 0.5
        return dist <= radius

    @staticmethod
    def _box_in_sphere(
        x1: float,
        x2: float,
        y1: float,
        y2: float,
        z1: float,
        z2: float,
        cx: float,
        cy: float,
        cz: float,
        radius: float,
    ) -> bool:
        """Check if box is completely in sphere."""
        # Check all 8 corners
        corners = [
            (x1, y1, z1),
            (x2, y1, z1),
            (x1, y2, z1),
            (x2, y2, z1),
            (x1, y1, z2),
            (x2, y1, z2),
            (x1, y2, z2),
            (x2, y2, z2),
        ]
        return all(OctreeModel._point_in_sphere(x, y, z, cx, cy, cz, radius) for x, y, z in corners)

    def get_material_volume(self) -> float:
        """Calculate remaining material volume."""
        return self._volume_recursive(self.root)

    def _volume_recursive(self, node: OctreeNode) -> float:
        """Recursively calculate volume."""
        if node.is_empty:
            return 0.0
        if node.is_full:
            return node.get_volume()

        if node.children is None:
            return node.get_volume()

        return sum(self._volume_recursive(child) for child in node.children)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "type": "octree",
            "bounds": {
                "x": [self.x_min, self.x_max],
                "y": [self.y_min, self.y_max],
                "z": [self.z_min, self.z_max],
            },
            "max_depth": self.max_depth,
            "material": {
                "name": self.material.name,
                "density": self.material.density,
            },
        }
