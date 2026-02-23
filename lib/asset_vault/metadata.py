"""
Asset Vault Metadata Extraction

Extract detailed metadata from 3D asset files.
Supports headless operation without Blender GUI.
"""

import re
import struct
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .enums import AssetFormat


def extract_metadata(
    asset_path: Path,
    format: Optional[AssetFormat] = None,
) -> Dict[str, Any]:
    """
    Extract metadata from an asset file.

    Dispatches to format-specific extractors.

    Args:
        asset_path: Path to the asset file
        format: Asset format (detected if not provided)

    Returns:
        Dictionary with metadata
    """
    if format is None:
        from .scanner import detect_format
        format = detect_format(asset_path)

    extractors = {
        AssetFormat.BLEND: extract_blend_metadata,
        AssetFormat.FBX: extract_fbx_metadata,
        AssetFormat.OBJ: extract_obj_metadata,
        AssetFormat.GLB: extract_glb_metadata,
        AssetFormat.GLTF: extract_gltf_metadata,
    }

    extractor = extractors.get(format, lambda p: {})
    return extractor(asset_path)


def extract_blend_metadata(path: Path) -> Dict[str, Any]:
    """
    Extract metadata from Blender .blend file.

    Uses bpy if available, falls back to binary header parsing.

    Args:
        path: Path to .blend file

    Returns:
        Dictionary with metadata
    """
    metadata: Dict[str, Any] = {
        "format": "blend",
        "objects": [],
        "collections": [],
        "materials": [],
    }

    # Try bpy first
    try:
        import bpy

        # Note: This only works if called from within Blender
        # or if bpy is available and properly configured
        # For headless operation, we'll parse the binary header
    except ImportError:
        pass

    # Parse blend header for basic info
    try:
        with open(path, "rb") as f:
            header = f.read(12)

            # Check magic
            if header[:7] == b"BLENDER":
                metadata["blender_version"] = header[7:11].decode("ascii", errors="ignore")
                metadata["pointer_size"] = "64-bit" if header[9:10] == b"-" else "32-bit"
                metadata["endianness"] = "little" if header[8:9] == b"v" else "big"

    except Exception as e:
        metadata["parse_error"] = str(e)

    return metadata


def extract_fbx_metadata(path: Path) -> Dict[str, Any]:
    """
    Extract metadata from FBX file.

    Parses FBX header and ASCII sections if present.

    Args:
        path: Path to FBX file

    Returns:
        Dictionary with metadata
    """
    metadata: Dict[str, Any] = {
        "format": "fbx",
        "geometry": {},
        "textures": [],
    }

    try:
        with open(path, "rb") as f:
            # Read header
            header = f.read(256)

            # Check FBX magic
            if b"Kaydara FBX Binary" in header[:23]:
                metadata["fbx_type"] = "binary"
                # Binary FBX - version info in header
                version_start = header.find(b"\x00\x00", 20)
                if version_start > 0:
                    version_bytes = header[version_start+1:version_start+5]
                    if len(version_bytes) >= 4:
                        version = struct.unpack("<I", version_bytes[:4])[0]
                        metadata["fbx_version"] = f"{version // 1000}.{version % 1000 // 100}"
            else:
                metadata["fbx_type"] = "ascii"

            # Try to find embedded texture references
            f.seek(0)
            content = f.read(65536)  # Read first 64KB

            # Find texture references
            texture_patterns = [
                rb'RelativeFilename:\s*"([^"]+)"',
                rb'FileName:\s*"([^"]+)"',
            ]
            textures = set()
            for pattern in texture_patterns:
                for match in re.finditer(pattern, content):
                    texture = match.group(1).decode("utf-8", errors="ignore")
                    if texture:
                        textures.add(texture)

            metadata["textures"] = list(textures)

    except Exception as e:
        metadata["parse_error"] = str(e)

    return metadata


def extract_obj_metadata(path: Path) -> Dict[str, Any]:
    """
    Extract metadata from OBJ file.

    Parses OBJ for geometry info without loading full file.

    Args:
        path: Path to OBJ file

    Returns:
        Dictionary with metadata
    """
    metadata: Dict[str, Any] = {
        "format": "obj",
        "geometry": {
            "vertices": 0,
            "faces": 0,
            "normals": 0,
            "texcoords": 0,
        },
        "groups": [],
        "objects": [],
        "materials": [],
        "material_library": None,
    }

    try:
        with open(path, "r", errors="ignore") as f:
            for line in f:
                line = line.strip()

                # Count geometry elements
                if line.startswith("v "):
                    metadata["geometry"]["vertices"] += 1
                elif line.startswith("f "):
                    metadata["geometry"]["faces"] += 1
                elif line.startswith("vn "):
                    metadata["geometry"]["normals"] += 1
                elif line.startswith("vt "):
                    metadata["geometry"]["texcoords"] += 1
                elif line.startswith("g "):
                    group = line[2:].strip()
                    if group:
                        metadata["groups"].append(group)
                elif line.startswith("o "):
                    obj = line[2:].strip()
                    if obj:
                        metadata["objects"].append(obj)
                elif line.startswith("usemtl "):
                    mat = line[7:].strip()
                    if mat and mat not in metadata["materials"]:
                        metadata["materials"].append(mat)
                elif line.startswith("mtllib "):
                    metadata["material_library"] = line[7:].strip()

    except Exception as e:
        metadata["parse_error"] = str(e)

    return metadata


def extract_glb_metadata(path: Path) -> Dict[str, Any]:
    """
    Extract metadata from GLB (binary glTF) file.

    Parses GLB header and JSON chunk.

    Args:
        path: Path to GLB file

    Returns:
        Dictionary with metadata
    """
    metadata: Dict[str, Any] = {
        "format": "glb",
        "meshes": 0,
        "materials": 0,
        "textures": 0,
        "nodes": [],
    }

    try:
        with open(path, "rb") as f:
            # GLB header
            magic = struct.unpack("<I", f.read(4))[0]
            if magic != 0x46546C67:  # "glTF" in little-endian
                metadata["error"] = "Not a valid GLB file"
                return metadata

            version = struct.unpack("<I", f.read(4))[0]
            metadata["gltf_version"] = version

            total_length = struct.unpack("<I", f.read(4))[0]

            # First chunk (JSON)
            chunk_length = struct.unpack("<I", f.read(4))[0]
            chunk_type = struct.unpack("<I", f.read(4))[0]

            if chunk_type == 0x4E4F534A:  # JSON
                json_data = f.read(chunk_length).decode("utf-8", errors="ignore")

                # Parse JSON for counts
                import json
                try:
                    gltf = json.loads(json_data)

                    metadata["meshes"] = len(gltf.get("meshes", []))
                    metadata["materials"] = len(gltf.get("materials", []))
                    metadata["textures"] = len(gltf.get("textures", []))

                    # Get node names
                    nodes = gltf.get("nodes", [])
                    metadata["nodes"] = [
                        n.get("name", f"node_{i}")
                        for i, n in enumerate(nodes)
                        if n.get("name")
                    ]

                except json.JSONDecodeError:
                    pass

    except Exception as e:
        metadata["parse_error"] = str(e)

    return metadata


def extract_gltf_metadata(path: Path) -> Dict[str, Any]:
    """
    Extract metadata from glTF JSON file.

    Args:
        path: Path to glTF file

    Returns:
        Dictionary with metadata
    """
    metadata: Dict[str, Any] = {
        "format": "gltf",
        "meshes": 0,
        "materials": 0,
        "textures": 0,
        "nodes": [],
    }

    try:
        import json
        with open(path, "r") as f:
            gltf = json.load(f)

        metadata["meshes"] = len(gltf.get("meshes", []))
        metadata["materials"] = len(gltf.get("materials", []))
        metadata["textures"] = len(gltf.get("textures", []))

        nodes = gltf.get("nodes", [])
        metadata["nodes"] = [
            n.get("name", f"node_{i}")
            for i, n in enumerate(nodes)
            if n.get("name")
        ]

        # Check for external buffers
        buffers = gltf.get("buffers", [])
        metadata["external_buffers"] = [
            b.get("uri") for b in buffers if b.get("uri")
        ]

    except Exception as e:
        metadata["parse_error"] = str(e)

    return metadata


def extract_dimensions(
    path: Path,
    format: AssetFormat,
) -> Optional[Tuple[float, float, float]]:
    """
    Extract bounding box dimensions from asset.

    Args:
        path: Path to asset file
        format: Asset format

    Returns:
        Tuple of (width, height, depth) in meters, or None if cannot determine
    """
    if format == AssetFormat.OBJ:
        return _extract_obj_dimensions(path)
    elif format in (AssetFormat.GLB, AssetFormat.GLTF):
        return _extract_gltf_dimensions(path)

    return None


def _extract_obj_dimensions(path: Path) -> Optional[Tuple[float, float, float]]:
    """Extract dimensions from OBJ file."""
    vertices = []

    try:
        with open(path, "r", errors="ignore") as f:
            for line in f:
                if line.startswith("v "):
                    parts = line.split()
                    if len(parts) >= 4:
                        try:
                            x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                            vertices.append((x, y, z))
                        except ValueError:
                            continue

        if not vertices:
            return None

        # Calculate bounding box
        xs = [v[0] for v in vertices]
        ys = [v[1] for v in vertices]
        zs = [v[2] for v in vertices]

        width = max(xs) - min(xs)
        height = max(ys) - min(ys)
        depth = max(zs) - min(zs)

        return (width, height, depth)

    except Exception:
        return None


def _extract_gltf_dimensions(path: Path) -> Optional[Tuple[float, float, float]]:
    """Extract dimensions from glTF/GLB file."""
    try:
        if path.suffix.lower() == ".glb":
            metadata = extract_glb_metadata(path)
        else:
            metadata = extract_gltf_metadata(path)

        # glTF doesn't store dimensions directly
        # Would need to parse mesh data
        return None

    except Exception:
        return None


def extract_materials(
    path: Path,
    format: AssetFormat,
) -> List[str]:
    """
    Extract material names from asset.

    Args:
        path: Path to asset file
        format: Asset format

    Returns:
        List of material names
    """
    if format == AssetFormat.OBJ:
        metadata = extract_obj_metadata(path)
        return metadata.get("materials", [])

    elif format in (AssetFormat.GLB, AssetFormat.GLTF):
        if format == AssetFormat.GLB:
            metadata = extract_glb_metadata(path)
        else:
            metadata = extract_gltf_metadata(path)
        return metadata.get("nodes", [])[:10]  # First 10 as material-like

    return []
