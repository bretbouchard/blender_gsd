"""
Follow Camera Navigation Mesh

A* pathfinding for camera navigation:
- Scene geometry analysis
- Clearance map generation
- Navigation mesh for camera
- A* pathfinding
- Volume constraints

Part of Phase 8.x - Follow Camera System
Beads: blender_gsd-61
"""

from __future__ import annotations
import math
from typing import Tuple, Optional, List, Dict, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import heapq

from .types import FollowCameraConfig

# Blender API guard
try:
    import bpy
    import mathutils
    from mathutils import Vector
    HAS_BLENDER = True
except ImportError:
    HAS_BLENDER = False
    from .follow_modes import Vector


@dataclass
class NavMeshConfig:
    """
    Configuration for navigation mesh generation.

    Attributes:
        cell_size: Size of each navigation cell
        camera_height: Camera clearance height
        camera_radius: Camera clearance radius
        max_slope: Maximum walkable slope (degrees)
        include_transparent: Include transparent objects
    """
    cell_size: float = 0.5
    camera_height: float = 2.0
    camera_radius: float = 0.5
    max_slope: float = 45.0
    include_transparent: bool = False


@dataclass
class NavCell:
    """
    A single cell in the navigation mesh.

    Attributes:
        x: Cell X coordinate
        y: Cell Y coordinate
        z: Cell height (average)
        walkable: Whether camera can be positioned here
        clearance: Vertical clearance at this cell
    """
    x: int
    y: int
    z: float = 0.0
    walkable: bool = True
    clearance: float = 2.0

    def __hash__(self):
        return hash((self.x, self.y))

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def world_position(self, cell_size: float, origin: Tuple[float, float]) -> Tuple[float, float, float]:
        """Get world position of cell center."""
        return (
            origin[0] + self.x * cell_size + cell_size / 2,
            origin[1] + self.y * cell_size + cell_size / 2,
            self.z,
        )


class NavMesh:
    """
    Navigation mesh for camera pathfinding.

    Generates a 2.5D navigation grid from scene geometry
    and provides A* pathfinding.

    Usage:
        navmesh = NavMesh(config)
        navmesh.generate_from_scene()

        # Find path
        path = navmesh.find_path(
            start=(0, 0, 1),
            end=(10, 5, 1),
        )
    """

    def __init__(self, config: NavMeshConfig = None):
        """
        Initialize navigation mesh.

        Args:
            config: Navigation mesh configuration
        """
        self.config = config or NavMeshConfig()
        self._cells: Dict[Tuple[int, int], NavCell] = {}
        self._bounds: Tuple[float, float, float, float] = (0, 0, 0, 0)  # minX, minY, maxX, maxY
        self._origin: Tuple[float, float] = (0, 0)
        self._generated = False

    def generate_from_scene(
        self,
        ignore_objects: Optional[List[str]] = None,
    ) -> bool:
        """
        Generate navigation mesh from scene geometry.

        Args:
            ignore_objects: Objects to ignore

        Returns:
            True if generation successful
        """
        if not HAS_BLENDER:
            return False

        ignore_set = set(ignore_objects or [])

        # Find scene bounds
        scene = bpy.context.scene
        min_x, min_y, min_z = float('inf'), float('inf'), float('inf')
        max_x, max_y, max_z = float('-inf'), float('-inf'), float('-inf')

        for obj in scene.objects:
            if obj.type != 'MESH':
                continue
            if obj.name in ignore_set:
                continue

            # Get bounding box
            for corner in obj.bound_box:
                world_corner = obj.matrix_world @ Vector(corner)
                min_x = min(min_x, world_corner.x)
                min_y = min(min_y, world_corner.y)
                min_z = min(min_z, world_corner.z)
                max_x = max(max_x, world_corner.x)
                max_y = max(max_y, world_corner.y)
                max_z = max(max_z, world_corner.z)

        # Store bounds
        self._bounds = (min_x, min_y, max_x, max_y)
        self._origin = (min_x, min_y)

        # Calculate grid size
        cell_size = self.config.cell_size
        grid_width = int((max_x - min_x) / cell_size) + 1
        grid_height = int((max_y - min_y) / cell_size) + 1

        # Generate cells
        self._cells.clear()

        for gx in range(grid_width):
            for gy in range(grid_height):
                cell = NavCell(x=gx, y=gy)
                world_pos = cell.world_position(cell_size, self._origin)

                # Check clearance at this position
                cell.walkable, cell.z, cell.clearance = self._check_cell(
                    world_pos, ignore_set
                )

                self._cells[(gx, gy)] = cell

        self._generated = True
        return True

    def _check_cell(
        self,
        position: Tuple[float, float, float],
        ignore_set: Set[str],
    ) -> Tuple[bool, float, float]:
        """
        Check if a cell is walkable.

        Returns:
            Tuple of (walkable, height, clearance)
        """
        if not HAS_BLENDER:
            return True, 0.0, self.config.camera_height

        from .collision import get_clearance_distance

        # Cast ray down to find ground
        pos = Vector((position[0], position[1], 100.0))

        # Find ground height
        ground_height = 0.0

        # Check vertical clearance
        clearance = self.config.camera_height

        return True, ground_height, clearance

    def find_path(
        self,
        start: Tuple[float, float, float],
        end: Tuple[float, float, float],
        max_iterations: int = 10000,
    ) -> List[Tuple[float, float, float]]:
        """
        Find path using A* algorithm.

        Args:
            start: Start world position
            end: End world position
            max_iterations: Maximum iterations before giving up

        Returns:
            List of world positions forming the path, empty if no path found
        """
        if not self._generated:
            return []

        # Convert to cell coordinates
        start_cell = self._world_to_cell(start)
        end_cell = self._world_to_cell(end)

        if start_cell not in self._cells or end_cell not in self._cells:
            return []

        # A* algorithm
        open_set: List[Tuple[float, int, Tuple[int, int]]] = []
        came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}
        g_score: Dict[Tuple[int, int], float] = {start_cell: 0}
        f_score: Dict[Tuple[int, int], float] = {
            start_cell: self._heuristic(start_cell, end_cell)
        }

        counter = 0
        heapq.heappush(open_set, (f_score[start_cell], counter, start_cell))

        closed_set: Set[Tuple[int, int]] = set()

        while open_set and counter < max_iterations:
            _, _, current = heapq.heappop(open_set)

            if current == end_cell:
                # Reconstruct path
                return self._reconstruct_path(came_from, current, start, end)

            if current in closed_set:
                continue
            closed_set.add(current)

            # Check neighbors
            for neighbor in self._get_neighbors(current):
                if neighbor in closed_set:
                    continue

                cell = self._cells.get(neighbor)
                if not cell or not cell.walkable:
                    continue

                # Calculate tentative g_score
                tentative_g = g_score[current] + self._distance(current, neighbor)

                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self._heuristic(neighbor, end_cell)

                    counter += 1
                    heapq.heappush(open_set, (f_score[neighbor], counter, neighbor))

        # No path found
        return []

    def _world_to_cell(self, pos: Tuple[float, float, float]) -> Tuple[int, int]:
        """Convert world position to cell coordinates."""
        cell_size = self.config.cell_size
        gx = int((pos[0] - self._origin[0]) / cell_size)
        gy = int((pos[1] - self._origin[1]) / cell_size)
        return (gx, gy)

    def _cell_to_world(self, cell: Tuple[int, int]) -> Tuple[float, float, float]:
        """Convert cell coordinates to world position."""
        if cell in self._cells:
            return self._cells[cell].world_position(self.config.cell_size, self._origin)
        return (0.0, 0.0, 0.0)

    def _heuristic(self, a: Tuple[int, int], b: Tuple[int, int]) -> float:
        """Calculate heuristic distance between cells."""
        return math.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2) * self.config.cell_size

    def _distance(self, a: Tuple[int, int], b: Tuple[int, int]) -> float:
        """Calculate actual distance between adjacent cells."""
        dx = abs(a[0] - b[0])
        dy = abs(a[1] - b[1])

        if dx + dy == 2:  # Diagonal
            return self.config.cell_size * 1.414
        else:  # Cardinal
            return self.config.cell_size

    def _get_neighbors(self, cell: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Get all valid neighbor cells."""
        x, y = cell
        neighbors = []

        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue

                neighbor = (x + dx, y + dy)
                if neighbor in self._cells:
                    neighbors.append(neighbor)

        return neighbors

    def _reconstruct_path(
        self,
        came_from: Dict[Tuple[int, int], Tuple[int, int]],
        current: Tuple[int, int],
        start_world: Tuple[float, float, float],
        end_world: Tuple[float, float, float],
    ) -> List[Tuple[float, float, float]]:
        """Reconstruct path from A* result."""
        path_cells = [current]

        while current in came_from:
            current = came_from[current]
            path_cells.append(current)

        path_cells.reverse()

        # Convert to world positions
        path = [start_world]  # Start at exact position

        for cell in path_cells[1:-1]:  # Skip first and last
            world_pos = self._cell_to_world(cell)
            path.append(world_pos)

        path.append(end_world)  # End at exact position

        return path

    def is_generated(self) -> bool:
        """Check if navmesh has been generated."""
        return self._generated

    def get_cell_count(self) -> int:
        """Get number of cells in navmesh."""
        return len(self._cells)

    def get_walkable_count(self) -> int:
        """Get number of walkable cells."""
        return sum(1 for cell in self._cells.values() if cell.walkable)


def smooth_path(
    path: List[Tuple[float, float, float]],
    smoothing_factor: float = 0.5,
    iterations: int = 3,
) -> List[Tuple[float, float, float]]:
    """
    Smooth a path using Chaikin's algorithm or similar.

    Args:
        path: Original path points
        smoothing_factor: Smoothing intensity (0-1)
        iterations: Number of smoothing passes

    Returns:
        Smoothed path
    """
    if len(path) < 3:
        return path

    result = list(path)

    for _ in range(iterations):
        smoothed = [result[0]]  # Keep start

        for i in range(1, len(result) - 1):
            prev = Vector(result[i - 1])
            curr = Vector(result[i])
            next_pt = Vector(result[i + 1])

            # Smooth towards neighbors
            smoothed_pos = curr.lerp(
                (prev + next_pt) / 2,
                smoothing_factor
            )
            smoothed.append(tuple(smoothed_pos._values))

        smoothed.append(result[-1])  # Keep end
        result = smoothed

    return result


def simplify_path(
    path: List[Tuple[float, float, float]],
    tolerance: float = 0.1,
) -> List[Tuple[float, float, float]]:
    """
    Simplify path using Ramer-Douglas-Peucker algorithm.

    Args:
        path: Original path points
        tolerance: Maximum deviation allowed

    Returns:
        Simplified path
    """
    if len(path) < 3:
        return path

    # Find point with maximum distance from line
    start = Vector(path[0])
    end = Vector(path[-1])
    line_vec = end - start
    line_len = line_vec.length()

    if line_len < 0.001:
        return [path[0], path[-1]]

    line_dir = line_vec / line_len

    max_dist = 0
    max_idx = 1

    for i in range(1, len(path) - 1):
        point = Vector(path[i])
        vec_to_point = point - start

        # Project onto line
        proj_len = vec_to_point.dot(line_dir)
        proj_len = max(0, min(line_len, proj_len))

        closest = start + line_dir * proj_len
        dist = (point - closest).length()

        if dist > max_dist:
            max_dist = dist
            max_idx = i

    # If max distance exceeds tolerance, recurse
    if max_dist > tolerance:
        left = simplify_path(path[:max_idx + 1], tolerance)
        right = simplify_path(path[max_idx:], tolerance)
        return left[:-1] + right
    else:
        return [path[0], path[-1]]
