"""
Asset Vault Scanner

Directory scanning and file detection for 3D assets.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from .enums import AssetFormat, EXTENSION_MAP
from .security import sanitize_path, SecurityConfig, SecurityError


# Supported file extensions
SUPPORTED_EXTENSIONS: Set[str] = {".blend", ".fbx", ".obj", ".glb", ".gltf", ".stl", ".abc", ".dae"}


def detect_format(file_path: Path) -> AssetFormat:
    """
    Detect asset format from file extension.

    Args:
        file_path: Path to the file

    Returns:
        AssetFormat enum value
    """
    ext = file_path.suffix.lower()
    return EXTENSION_MAP.get(ext, AssetFormat.UNKNOWN)


def scan_directory(
    directory: Path,
    recursive: bool = True,
    config: Optional[SecurityConfig] = None,
    extensions: Optional[Set[str]] = None,
) -> List[Path]:
    """
    Scan a directory for 3D asset files.

    Args:
        directory: Directory to scan
        recursive: Whether to scan subdirectories
        config: Security configuration for access validation
        extensions: Custom set of extensions to filter (default: SUPPORTED_EXTENSIONS)

    Returns:
        List of valid asset paths

    Raises:
        SecurityError: If directory is not in allowed paths
    """
    # Sanitize directory path
    directory = sanitize_path(directory)

    if not directory.exists():
        return []

    if not directory.is_dir():
        raise ValueError(f"Not a directory: {directory}")

    extensions = extensions or SUPPORTED_EXTENSIONS
    config = config or SecurityConfig()
    assets: List[Path] = []

    # Walk directory
    if recursive:
        walker = directory.rglob("*")
    else:
        walker = directory.glob("*")

    for path in walker:
        if not path.is_file():
            continue

        # Check extension
        if path.suffix.lower() not in extensions:
            continue

        # Validate file access
        is_valid, _ = validate_file_access(path, config)
        if is_valid:
            assets.append(path)

    return assets


def scan_library(
    library_path: Path,
    config: Optional[SecurityConfig] = None,
) -> Dict[str, List[Path]]:
    """
    Scan a library directory, organizing assets by pack/subdirectory.

    Top-level subdirectories are treated as "packs".

    Args:
        library_path: Root directory of the asset library
        config: Security configuration

    Returns:
        Dictionary mapping pack names to lists of asset paths
    """
    library_path = sanitize_path(library_path)

    if not library_path.exists() or not library_path.is_dir():
        return {}

    packs: Dict[str, List[Path]] = {}

    # Scan each top-level subdirectory as a pack
    for item in library_path.iterdir():
        if not item.is_dir():
            continue

        pack_name = item.name
        pack_assets = scan_directory(item, recursive=True, config=config)

        if pack_assets:
            packs[pack_name] = pack_assets

    # Also scan files directly in root (no pack)
    root_assets = []
    for item in library_path.iterdir():
        if item.is_file() and item.suffix.lower() in SUPPORTED_EXTENSIONS:
            is_valid, _ = validate_file_access(item, config or SecurityConfig())
            if is_valid:
                root_assets.append(item)

    if root_assets:
        packs["_root_"] = root_assets

    return packs


def get_file_info(path: Path) -> Dict[str, Any]:
    """
    Get basic file information without parsing.

    Fast operation that works without Blender.

    Args:
        path: Path to the file

    Returns:
        Dictionary with file metadata
    """
    try:
        stat = path.stat()
        return {
            "path": str(path),
            "name": path.name,
            "stem": path.stem,
            "extension": path.suffix.lower(),
            "size_bytes": stat.st_size,
            "size_mb": stat.st_size / (1024 * 1024),
            "modified_time": stat.st_mtime,
            "is_readable": True,
            "format": detect_format(path).value,
        }
    except PermissionError:
        return {
            "path": str(path),
            "name": path.name,
            "stem": path.stem,
            "extension": path.suffix.lower(),
            "is_readable": False,
            "error": "Permission denied",
        }
    except Exception as e:
        return {
            "path": str(path),
            "name": path.name,
            "stem": path.stem,
            "extension": path.suffix.lower(),
            "is_readable": False,
            "error": str(e),
        }


def count_assets(
    directory: Path,
    recursive: bool = True,
    config: Optional[SecurityConfig] = None,
) -> Dict[str, int]:
    """
    Count assets by format in a directory.

    Args:
        directory: Directory to scan
        recursive: Whether to scan subdirectories
        config: Security configuration

    Returns:
        Dictionary mapping format names to counts
    """
    assets = scan_directory(directory, recursive=recursive, config=config)

    counts: Dict[str, int] = {}
    for asset_path in assets:
        format_name = detect_format(asset_path).value
        counts[format_name] = counts.get(format_name, 0) + 1

    return counts
