"""
Scan Import Module

Provides parsers and utilities for importing LiDAR/scan data from
various sources including Stanford PLY and Wavefront OBJ formats.

Includes:
- PLYParser: Parse Stanford PLY files (ASCII and binary)
- OBJParser: Parse Wavefront OBJ files
- FloorDetector: RANSAC-based floor plane detection
- ScaleDetector: Scale calibration from known references
- ScanImporter: Main import interface
"""

from __future__ import annotations

import os
import struct
import math
import random
from dataclasses import dataclass, field
from typing import Dict, Any, Tuple, List, Optional, BinaryIO

from .types import FloorPlane, ScaleCalibration, ScanData


# Supported scan formats with their properties
SCAN_FORMATS: Dict[str, Dict[str, Any]] = {
    "ply": {
        "name": "Stanford PLY",
        "extensions": [".ply"],
        "supports_points": True,
        "supports_mesh": True,
        "supports_color": True,
        "supports_normals": True,
    },
    "obj": {
        "name": "Wavefront OBJ",
        "extensions": [".obj"],
        "supports_points": False,
        "supports_mesh": True,
        "supports_color": False,
        "supports_normals": True,
    },
    "pts": {
        "name": "PTS Point Cloud",
        "extensions": [".pts"],
        "supports_points": True,
        "supports_mesh": False,
        "supports_color": False,
        "supports_normals": False,
    },
    "xyz": {
        "name": "XYZ ASCII",
        "extensions": [".xyz"],
        "supports_points": True,
        "supports_mesh": False,
        "supports_color": False,
        "supports_normals": True,
    },
}


class PLYParser:
    """
    Parser for Stanford PLY format files.

    Supports both ASCII and binary formats with optional color
    and normal data.

    Example:
        parser = PLYParser()
        vertices, colors, normals = parser.parse("scan.ply")
        metadata = parser.get_metadata()
    """

    def __init__(self) -> None:
        self.format: str = "ascii"
        self.vertex_count: int = 0
        self.face_count: int = 0
        self.has_color: bool = False
        self.has_normals: bool = False
        self.properties: List[str] = []

    def parse(self, filepath: str) -> Tuple[List[Tuple[float, float, float]],
                                            List[Tuple[int, int, int]],
                                            List[Tuple[float, float, float]]]:
        """
        Parse PLY file and extract vertex data.

        Args:
            filepath: Path to PLY file

        Returns:
            Tuple of (vertices, colors, normals) where:
            - vertices: List of (x, y, z) coordinates
            - colors: List of (r, g, b) values (0-255)
            - normals: List of (nx, ny, nz) normal vectors
        """
        with open(filepath, "rb") as f:
            self._parse_header(f)
            if self.format == "ascii":
                return self._parse_ascii(f)
            else:
                return self._parse_binary(f, self.format)

    def _parse_header(self, f: BinaryIO) -> None:
        """Parse PLY header to get format and properties."""
        self.properties = []

        line = f.readline().decode("ascii").strip()
        if line != "ply":
            raise ValueError("Not a valid PLY file")

        while True:
            line = f.readline().decode("ascii").strip()
            parts = line.split()

            if parts[0] == "format":
                self.format = parts[1]
            elif parts[0] == "element":
                if parts[1] == "vertex":
                    self.vertex_count = int(parts[2])
                elif parts[1] == "face":
                    self.face_count = int(parts[2])
            elif parts[0] == "property":
                prop_name = parts[-1]
                self.properties.append(prop_name)
                if prop_name in ("red", "green", "blue", "r", "g", "b"):
                    self.has_color = True
                elif prop_name in ("nx", "ny", "nz"):
                    self.has_normals = True
            elif parts[0] == "end_header":
                break

    def _parse_ascii(self, f: BinaryIO) -> Tuple[List[Tuple[float, float, float]],
                                                  List[Tuple[int, int, int]],
                                                  List[Tuple[float, float, float]]]:
        """Parse ASCII format PLY data."""
        vertices = []
        colors = []
        normals = []

        for _ in range(self.vertex_count):
            line = f.readline().decode("ascii").strip()
            parts = line.split()

            vertex = [0.0, 0.0, 0.0]
            color = [128, 128, 128]
            normal = [0.0, 0.0, 1.0]

            for i, prop in enumerate(self.properties):
                if i >= len(parts):
                    break
                value = parts[i]

                if prop in ("x", "y", "z"):
                    idx = {"x": 0, "y": 1, "z": 2}[prop]
                    vertex[idx] = float(value)
                elif prop in ("nx", "ny", "nz"):
                    idx = {"nx": 0, "ny": 1, "nz": 2}[prop]
                    normal[idx] = float(value)
                elif prop in ("red", "r"):
                    color[0] = int(float(value))
                elif prop in ("green", "g"):
                    color[1] = int(float(value))
                elif prop in ("blue", "b"):
                    color[2] = int(float(value))

            vertices.append(tuple(vertex))
            colors.append(tuple(color))
            normals.append(tuple(normal))

        return vertices, colors, normals

    def _parse_binary(self, f: BinaryIO, fmt: str) -> Tuple[List[Tuple[float, float, float]],
                                                             List[Tuple[int, int, int]],
                                                             List[Tuple[float, float, float]]]:
        """Parse binary format PLY data."""
        vertices = []
        colors = []
        normals = []

        # Determine byte order
        endian = "<" if fmt == "binary_little_endian" else ">"

        for _ in range(self.vertex_count):
            vertex = [0.0, 0.0, 0.0]
            color = [128, 128, 128]
            normal = [0.0, 0.0, 1.0]

            for prop in self.properties:
                if prop in ("x", "y", "z"):
                    value = struct.unpack(endian + "f", f.read(4))[0]
                    idx = {"x": 0, "y": 1, "z": 2}[prop]
                    vertex[idx] = value
                elif prop in ("nx", "ny", "nz"):
                    value = struct.unpack(endian + "f", f.read(4))[0]
                    idx = {"nx": 0, "ny": 1, "nz": 2}[prop]
                    normal[idx] = value
                elif prop in ("red", "r", "green", "g", "blue", "b"):
                    value = struct.unpack(endian + "B", f.read(1))[0]
                    if prop in ("red", "r"):
                        color[0] = value
                    elif prop in ("green", "g"):
                        color[1] = value
                    else:
                        color[2] = value
                else:
                    # Unknown property - try float
                    f.read(4)

            vertices.append(tuple(vertex))
            colors.append(tuple(color))
            normals.append(tuple(normal))

        return vertices, colors, normals

    def get_metadata(self) -> Dict[str, Any]:
        """Get parsed metadata."""
        return {
            "format": self.format,
            "vertex_count": self.vertex_count,
            "face_count": self.face_count,
            "has_color": self.has_color,
            "has_normals": self.has_normals,
            "properties": self.properties,
        }


class OBJParser:
    """
    Parser for Wavefront OBJ format files.

    Supports vertices, normals, and faces. Returns vertex data
    suitable for scan processing.

    Example:
        parser = OBJParser()
        vertices, normals, faces = parser.parse("model.obj")
        metadata = parser.get_metadata()
    """

    def __init__(self) -> None:
        self.vertex_count: int = 0
        self.face_count: int = 0
        self.has_normals: bool = False
        self.normal_count: int = 0

    def parse(self, filepath: str) -> Tuple[List[Tuple[float, float, float]],
                                            List[Tuple[float, float, float]],
                                            List[Tuple[int, ...]]]:
        """
        Parse OBJ file and extract geometry data.

        Args:
            filepath: Path to OBJ file

        Returns:
            Tuple of (vertices, normals, faces) where:
            - vertices: List of (x, y, z) coordinates
            - normals: List of (nx, ny, nz) vectors
            - faces: List of vertex index tuples
        """
        vertices = []
        normals = []
        faces = []

        with open(filepath, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                parts = line.split()
                if not parts:
                    continue

                cmd = parts[0]

                if cmd == "v":
                    # Vertex: v x y z [w]
                    x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                    vertices.append((x, y, z))
                elif cmd == "vn":
                    # Normal: vn x y z
                    nx, ny, nz = float(parts[1]), float(parts[2]), float(parts[3])
                    normals.append((nx, ny, nz))
                    self.has_normals = True
                elif cmd == "f":
                    # Face: f v1/vt1/vn1 v2/vt2/vn2 ...
                    face_verts = []
                    for i in range(1, len(parts)):
                        # Parse vertex index (format: v, v/vt, v/vt/vn, v//vn)
                        indices = parts[i].split("/")
                        v_idx = int(indices[0])
                        # OBJ indices are 1-based
                        if v_idx > 0:
                            face_verts.append(v_idx - 1)
                        else:
                            # Negative index
                            face_verts.append(len(vertices) + v_idx)
                    faces.append(tuple(face_verts))

        self.vertex_count = len(vertices)
        self.normal_count = len(normals)
        self.face_count = len(faces)

        return vertices, normals, faces

    def get_metadata(self) -> Dict[str, Any]:
        """Get parsed metadata."""
        return {
            "vertex_count": self.vertex_count,
            "face_count": self.face_count,
            "has_normals": self.has_normals,
            "normal_count": self.normal_count,
        }


class FloorDetector:
    """
    RANSAC-based floor plane detector.

    Uses Random Sample Consensus to find the dominant horizontal
    plane in point cloud data, typically representing the floor.

    Example:
        detector = FloorDetector()
        floor = detector.detect(vertices, threshold=0.05)
        if floor.confidence > 0.8:
            print(f"Floor detected with {floor.inlier_count} points")
    """

    def __init__(self,
                 max_iterations: int = 1000,
                 threshold: float = 0.05,
                 min_inliers: int = 100) -> None:
        """
        Initialize floor detector.

        Args:
            max_iterations: Maximum RANSAC iterations
            threshold: Distance threshold for inliers (meters)
            min_inliers: Minimum inliers for valid detection
        """
        self.max_iterations = max_iterations
        self.threshold = threshold
        self.min_inliers = min_inliers

    def detect(self,
               vertices: List[Tuple[float, float, float]],
               prefer_horizontal: bool = True) -> FloorPlane:
        """
        Detect floor plane from point cloud vertices.

        Args:
            vertices: List of (x, y, z) coordinates
            prefer_horizontal: Bias toward horizontal planes

        Returns:
            FloorPlane with detected plane data
        """
        if len(vertices) < 3:
            return FloorPlane(confidence=0.0)

        best_plane = FloorPlane(confidence=0.0)
        best_inliers: List[int] = []

        for _ in range(self.max_iterations):
            # Sample 3 random points
            if len(vertices) < 3:
                continue
            sample_indices = random.sample(range(len(vertices)), 3)
            p1 = vertices[sample_indices[0]]
            p2 = vertices[sample_indices[1]]
            p3 = vertices[sample_indices[2]]

            # Compute plane normal via cross product
            v1 = (p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2])
            v2 = (p3[0] - p1[0], p3[1] - p1[1], p3[2] - p1[2])

            # Cross product for normal
            nx = v1[1] * v2[2] - v1[2] * v2[1]
            ny = v1[2] * v2[0] - v1[0] * v2[2]
            nz = v1[0] * v2[1] - v1[1] * v2[0]

            # Normalize
            length = math.sqrt(nx * nx + ny * ny + nz * nz)
            if length < 1e-10:
                continue
            nx, ny, nz = nx / length, ny / length, nz / length

            # Ensure normal points up (positive Z)
            if nz < 0:
                nx, ny, nz = -nx, -ny, -nz

            # Skip if not roughly horizontal (optional bias)
            if prefer_horizontal and abs(nz) < 0.7:
                continue

            # Compute distance from origin
            d = -(nx * p1[0] + ny * p1[1] + nz * p1[2])

            # Count inliers
            inliers = []
            for i, v in enumerate(vertices):
                dist = abs(nx * v[0] + ny * v[1] + nz * v[2] + d)
                if dist < self.threshold:
                    inliers.append(i)

            # Update best if more inliers found
            if len(inliers) > len(best_inliers):
                best_inliers = inliers
                best_plane = FloorPlane(
                    normal=(nx, ny, nz),
                    distance=d,
                    confidence=len(inliers) / len(vertices),
                    inlier_count=len(inliers),
                    rotation_euler=self._compute_rotation_to_xy(nx, ny, nz),
                )

        # Validate minimum inliers
        if best_plane.inlier_count < self.min_inliers:
            best_plane.confidence = 0.0

        return best_plane

    def _compute_rotation_to_xy(self, nx: float, ny: float, nz: float) -> Tuple[float, float, float]:
        """
        Compute Euler rotation to align plane normal to Z-up.

        Args:
            nx, ny, nz: Plane normal components

        Returns:
            Euler angles (rx, ry, rz) in radians
        """
        # Rotation to align normal with Z-axis
        # Using spherical to Euler conversion
        ry = math.atan2(nx, nz)
        rx = -math.asin(ny) if abs(ny) <= 1.0 else -math.copysign(math.pi / 2, ny)
        return (rx, ry, 0.0)


class ScaleDetector:
    """
    Scale calibration from known references.

    Provides methods to calibrate scan scale using known distances
    or ArUco markers in the scanned environment.

    Example:
        detector = ScaleDetector()
        calibration = detector.calibrate_from_distance(
            (0, 0, 0), (1, 0, 0), known_distance=1.0
        )
        print(f"Scale factor: {calibration.scale_factor}")
    """

    def __init__(self, min_confidence: float = 0.5) -> None:
        """
        Initialize scale detector.

        Args:
            min_confidence: Minimum confidence threshold
        """
        self.min_confidence = min_confidence

    def calibrate_from_distance(self,
                                p1: Tuple[float, float, float],
                                p2: Tuple[float, float, float],
                                known_distance: float) -> ScaleCalibration:
        """
        Calibrate scale from known distance between two points.

        Args:
            p1: First point in scan coordinates
            p2: Second point in scan coordinates
            known_distance: Real-world distance between points

        Returns:
            ScaleCalibration with computed scale factor
        """
        if known_distance <= 0:
            return ScaleCalibration(confidence=0.0)

        # Compute measured distance
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        dz = p2[2] - p1[2]
        measured_distance = math.sqrt(dx * dx + dy * dy + dz * dz)

        if measured_distance <= 0:
            return ScaleCalibration(confidence=0.0)

        scale_factor = known_distance / measured_distance
        confidence = min(1.0, 1.0 / (1.0 + abs(scale_factor - 1.0)))

        return ScaleCalibration(
            scale_factor=scale_factor,
            reference_type="distance",
            reference_value=known_distance,
            measured_value=measured_distance,
            confidence=confidence,
        )

    def calibrate_from_aruco(self,
                             marker_size_meters: float,
                             detected_corners: List[Tuple[float, float, float]]) -> ScaleCalibration:
        """
        Calibrate scale from ArUco marker.

        Args:
            marker_size_meters: Real marker size in meters
            detected_corners: Four corners of detected marker

        Returns:
            ScaleCalibration with computed scale factor
        """
        if len(detected_corners) != 4:
            return ScaleCalibration(confidence=0.0)

        # Average edge lengths
        edges = []
        for i in range(4):
            p1 = detected_corners[i]
            p2 = detected_corners[(i + 1) % 4]
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            dz = p2[2] - p1[2]
            edges.append(math.sqrt(dx * dx + dy * dy + dz * dz))

        avg_edge = sum(edges) / len(edges)
        if avg_edge <= 0:
            return ScaleCalibration(confidence=0.0)

        scale_factor = marker_size_meters / avg_edge
        confidence = min(1.0, 1.0 / (1.0 + abs(scale_factor - 1.0)))

        return ScaleCalibration(
            scale_factor=scale_factor,
            reference_type="aruco",
            reference_value=marker_size_meters,
            measured_value=avg_edge,
            confidence=confidence,
        )


class ScanImporter:
    """
    Main scan import interface.

    Provides unified interface for importing scan data from various
    formats with automatic floor detection and scale calibration.

    Example:
        importer = ScanImporter()
        scan = importer.import_scan("room_scan.ply", detect_floor=True)
        print(f"Imported {scan.point_count} points")

        # Calibrate scale
        importer.calibrate_scale_distance(scan, p1, p2, 1.0)

        # Align to ground
        importer.align_to_ground(scan)
    """

    def __init__(self) -> None:
        """Initialize scan importer."""
        self.floor_detector = FloorDetector()
        self.scale_detector = ScaleDetector()

    def import_scan(self,
                    filepath: str,
                    detect_floor: bool = True,
                    auto_scale: bool = False) -> ScanData:
        """
        Import scan from file.

        Args:
            filepath: Path to scan file
            detect_floor: Automatically detect floor plane
            auto_scale: Apply auto-scaling (not yet implemented)

        Returns:
            ScanData with imported scan information
        """
        ext = os.path.splitext(filepath)[1].lower()

        if ext == ".ply":
            vertices, colors, normals = self._import_ply(filepath)
            source_format = "ply"
        elif ext == ".obj":
            vertices, normals, faces = self._import_obj(filepath)
            colors = []
            source_format = "obj"
        else:
            raise ValueError(f"Unsupported format: {ext}")

        # Compute bounding box
        if vertices:
            bounds_min, bounds_max = self._compute_bounds(vertices)
        else:
            bounds_min = (0.0, 0.0, 0.0)
            bounds_max = (1.0, 1.0, 1.0)

        # Detect floor if requested
        floor = None
        if detect_floor and vertices:
            floor = self.floor_detector.detect(vertices)

        scan = ScanData(
            name=os.path.basename(filepath),
            source_path=filepath,
            source_format=source_format,
            point_count=len(vertices),
            vertex_count=len(vertices),
            bounds_min=bounds_min,
            bounds_max=bounds_max,
            floor=floor,
            is_point_cloud=len(vertices) > 0,
            has_color=len(colors) > 0,
            has_normals=len(normals) > 0 and any(n != (0.0, 0.0, 1.0) for n in normals),
        )

        return scan

    def _import_ply(self, filepath: str) -> Tuple[List[Tuple[float, float, float]],
                                                   List[Tuple[int, int, int]],
                                                   List[Tuple[float, float, float]]]:
        """Import PLY file."""
        parser = PLYParser()
        return parser.parse(filepath)

    def _import_obj(self, filepath: str) -> Tuple[List[Tuple[float, float, float]],
                                                   List[Tuple[float, float, float]],
                                                   List[Tuple[int, ...]]]:
        """Import OBJ file."""
        parser = OBJParser()
        return parser.parse(filepath)

    def _compute_bounds(self,
                        vertices: List[Tuple[float, float, float]]) -> Tuple[Tuple[float, float, float],
                                                                               Tuple[float, float, float]]:
        """Compute bounding box from vertices."""
        if not vertices:
            return (0.0, 0.0, 0.0), (1.0, 1.0, 1.0)

        min_x = min_y = min_z = float("inf")
        max_x = max_y = max_z = float("-inf")

        for v in vertices:
            min_x = min(min_x, v[0])
            min_y = min(min_y, v[1])
            min_z = min(min_z, v[2])
            max_x = max(max_x, v[0])
            max_y = max(max_y, v[1])
            max_z = max(max_z, v[2])

        return (min_x, min_y, min_z), (max_x, max_y, max_z)

    def calibrate_scale_distance(self,
                                 scan: ScanData,
                                 p1: Tuple[float, float, float],
                                 p2: Tuple[float, float, float],
                                 known_distance: float) -> ScaleCalibration:
        """
        Calibrate scan scale from known distance.

        Args:
            scan: ScanData to calibrate
            p1: First point in scan coordinates
            p2: Second point in scan coordinates
            known_distance: Real-world distance between points

        Returns:
            ScaleCalibration with computed scale factor
        """
        calibration = self.scale_detector.calibrate_from_distance(p1, p2, known_distance)
        scan.scale = calibration
        return calibration

    def align_to_ground(self, scan: ScanData) -> bool:
        """
        Align scan so floor is at Z=0.

        Modifies scan bounds to place floor at ground level.

        Args:
            scan: ScanData to align

        Returns:
            True if alignment successful
        """
        if not scan.floor or scan.floor.confidence <= 0:
            return False

        # Move bounds so floor distance becomes 0
        offset = scan.floor.distance
        scan.bounds_min = (
            scan.bounds_min[0],
            scan.bounds_min[1],
            scan.bounds_min[2] - offset,
        )
        scan.bounds_max = (
            scan.bounds_max[0],
            scan.bounds_max[1],
            scan.bounds_max[2] - offset,
        )

        # Update floor distance
        scan.floor.distance = 0.0

        return True


# Convenience functions for specific scan sources

def import_polycam(filepath: str, detect_floor: bool = True) -> ScanData:
    """
    Import Polycam scan.

    Args:
        filepath: Path to Polycam export file (PLY or OBJ)
        detect_floor: Automatically detect floor plane

    Returns:
        ScanData with imported scan
    """
    importer = ScanImporter()
    scan = importer.import_scan(filepath, detect_floor=detect_floor)
    scan.name = f"polycam_{scan.name}"
    return scan


def import_reality_scan(filepath: str, detect_floor: bool = True) -> ScanData:
    """
    Import RealityCapture/Meta scan.

    Args:
        filepath: Path to scan file (PLY or OBJ)
        detect_floor: Automatically detect floor plane

    Returns:
        ScanData with imported scan
    """
    importer = ScanImporter()
    scan = importer.import_scan(filepath, detect_floor=detect_floor)
    scan.name = f"reality_{scan.name}"
    return scan
