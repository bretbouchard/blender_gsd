"""
Cryptomatte Support

Utilities for working with Cryptomatte mattes from EXR renders.

Cryptomatte is a system for creating ID mattes from renders.
See: https://github.com/Psyop/Cryptomatte

Part of Phase 12.1: Compositor (REQ-COMP-04)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Set
import json
import struct
import hashlib
import math


@dataclass
class CryptomatteManifestEntry:
    """A single entry in the cryptomatte manifest."""
    name: str
    hash: str
    rank: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "hash": self.hash,
            "rank": self.rank,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CryptomatteManifestEntry":
        return cls(
            name=data.get("name", ""),
            hash=data.get("hash", ""),
            rank=data.get("rank", 0),
        )


@dataclass
class CryptomatteManifest:
    """Cryptomatte manifest containing object names and hashes."""
    layer_name: str
    entries: List[CryptomatteManifestEntry] = field(default_factory=list)
    _hash_to_name: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        self._rebuild_index()

    def _rebuild_index(self) -> None:
        """Rebuild the hash lookup index."""
        self._hash_to_name = {e.hash: e.name for e in self.entries}

    def add_entry(self, name: str, hash_value: str, rank: int = 0) -> None:
        """Add an entry to the manifest."""
        entry = CryptomatteManifestEntry(name=name, hash=hash_value, rank=rank)
        self.entries.append(entry)
        self._hash_to_name[hash_value] = name

    def get_name(self, hash_value: str) -> Optional[str]:
        """Get object name from hash."""
        return self._hash_to_name.get(hash_value)

    def get_hash(self, name: str) -> Optional[str]:
        """Get hash for object name."""
        for entry in self.entries:
            if entry.name == name:
                return entry.hash
        return None

    def get_all_names(self) -> List[str]:
        """Get all object names."""
        return [e.name for e in self.entries]

    def get_entries_by_rank(self, rank: int) -> List[CryptomatteManifestEntry]:
        """Get all entries at a specific rank."""
        return [e for e in self.entries if e.rank == rank]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "layer_name": self.layer_name,
            "entries": [e.to_dict() for e in self.entries],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CryptomatteManifest":
        manifest = cls(layer_name=data.get("layer_name", ""))
        manifest.entries = [CryptomatteManifestEntry.from_dict(e) for e in data.get("entries", [])]
        manifest._rebuild_index()
        return manifest


# ==================== Hash Functions ====================

def hash_object_name(name: str) -> str:
    """
    Generate a cryptomatte hash from an object name.

    Cryptomatte uses the first 32 bits of MD5 hash.
    """
    md5 = hashlib.md5(name.encode('utf-8')).digest()
    # Take first 4 bytes (32 bits) and convert to hex
    hash_int = struct.unpack('<I', md5[:4])[0]
    return format(hash_int, '08x')


def hash_to_float(hash_value: str) -> float:
    """
    Convert a cryptomatte hash to a float value.

    The float representation is used in the EXR channels.
    """
    hash_int = int(hash_value, 16)
    # Convert to IEEE 754 float
    packed = struct.pack('<I', hash_int)
    return struct.unpack('<f', packed)[0]


def float_to_hash(float_value: float) -> str:
    """
    Convert a float value back to a cryptomatte hash.
    """
    packed = struct.pack('<f', float_value)
    hash_int = struct.unpack('<I', packed)[0]
    return format(hash_int, '08x')


# ==================== Manifest Loading ====================

def load_manifest_from_json(path: str) -> Optional[CryptomatteManifest]:
    """Load a cryptomatte manifest from a JSON file."""
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        return CryptomatteManifest.from_dict(data)
    except Exception as e:
        print(f"Failed to load manifest: {e}")
        return None


def load_manifest_from_exr_sidecar(exr_path: str) -> Optional[CryptomatteManifest]:
    """
    Load manifest from EXR sidecar JSON file.

    Sidecar files are named: <exr_path>.manifest.json
    """
    sidecar = f"{exr_path}.manifest.json"
    return load_manifest_from_json(sidecar)


def parse_manifest_from_exr_header(exr_path: str) -> Optional[CryptomatteManifest]:
    """
    Parse manifest embedded in EXR header.

    Note: This requires OpenEXR library. For now, returns None.
    In production, use OpenEXR or similar library.
    """
    # Would require OpenEXR library:
    # import OpenEXR
    # exr_file = OpenEXR.InputFile(exr_path)
    # header = exr_file.header()
    # Parse cryptomatte header attributes

    print("EXR header parsing requires OpenEXR library")
    return None


def create_cryptomatte_manifest(
    objects: List[str],
    layer_name: str = "cryptomatte00",
) -> CryptomatteManifest:
    """
    Create a cryptomatte manifest from a list of object names.
    """
    manifest = CryptomatteManifest(layer_name=layer_name)

    for obj_name in objects:
        hash_value = hash_object_name(obj_name)
        manifest.add_entry(obj_name, hash_value)

    return manifest


def save_manifest(manifest: CryptomatteManifest, path: str) -> bool:
    """Save a manifest to a JSON file."""
    try:
        with open(path, 'w') as f:
            json.dump(manifest.to_dict(), f, indent=2)
        return True
    except Exception as e:
        print(f"Failed to save manifest: {e}")
        return False


# ==================== Matte Extraction ====================

@dataclass
class MatteResult:
    """Result of matte extraction."""
    success: bool
    matte: Optional[Any] = None  # Would be numpy array in practice
    error: str = ""
    coverage: float = 0.0  # How much of the matte was found


def extract_matte_for_object(
    manifest: CryptomatteManifest,
    object_name: str,
    exr_data: Optional[Any] = None,  # Would be EXR channel data
    rank: int = 0,
) -> MatteResult:
    """
    Extract a matte for a specific object.

    Args:
        manifest: The cryptomatte manifest
        object_name: Name of object to extract
        exr_data: The EXR channel data (would be numpy array)
        rank: Which rank to extract (0-6 typically)

    Returns:
        MatteResult with the extracted matte
    """
    # Get hash for object
    hash_value = manifest.get_hash(object_name)
    if not hash_value:
        return MatteResult(
            success=False,
            error=f"Object '{object_name}' not found in manifest"
        )

    # Convert hash to float for comparison
    target_float = hash_to_float(hash_value)

    # In a real implementation, this would:
    # 1. Load the appropriate rank channel from EXR
    # 2. Compare against target_float with tolerance
    # 3. Create binary or graded matte

    # Placeholder implementation
    return MatteResult(
        success=True,
        matte=None,
        coverage=1.0,
    )


def extract_matte_for_objects(
    manifest: CryptomatteManifest,
    object_names: List[str],
    exr_data: Optional[Any] = None,
    combine_mode: str = "union",
) -> MatteResult:
    """
    Extract a combined matte for multiple objects.

    Args:
        manifest: The cryptomatte manifest
        object_names: Names of objects to extract
        exr_data: The EXR channel data
        combine_mode: How to combine mattes ("union", "intersection", "difference")

    Returns:
        MatteResult with the combined matte
    """
    if not object_names:
        return MatteResult(success=False, error="No objects specified")

    # Extract individual mattes
    mattes = []
    for name in object_names:
        result = extract_matte_for_object(manifest, name, exr_data)
        if result.success and result.matte is not None:
            mattes.append(result.matte)

    if not mattes:
        return MatteResult(success=False, error="No valid mattes extracted")

    # Combine based on mode
    # In real implementation:
    # if combine_mode == "union":
    #     combined = np.maximum.reduce(mattes)
    # elif combine_mode == "intersection":
    #     combined = np.minimum.reduce(mattes)
    # elif combine_mode == "difference":
    #     combined = mattes[0]
    #     for m in mattes[1:]:
    #         combined = np.maximum(0, combined - m)

    return MatteResult(
        success=True,
        matte=None,  # Would be combined matte
        coverage=len(mattes) / len(object_names),
    )


# ==================== Utilities ====================

def get_cryptomatte_layer_names(exr_path: str) -> List[str]:
    """
    Get list of cryptomatte layer names from an EXR file.

    Layer names are typically: cryptomatte00, cryptomatte01, etc.
    """
    # Would require OpenEXR library to read channel names
    return []


def get_cryptomatte_info(exr_path: str) -> Dict[str, Any]:
    """
    Get cryptomatte information from an EXR file.

    Returns dict with layer names, manifest info, etc.
    """
    # Would require OpenEXR library
    return {
        "has_cryptomatte": False,
        "layers": [],
        "manifests": [],
    }


def rank_to_channels(rank: int) -> List[str]:
    """
    Get the channel names for a cryptomatte rank.

    Each rank has 3 channels: R (hash), G (coverage), B (unused)
    """
    return [
        f"cryptomatte{rank:02d}.R",
        f"cryptomatte{rank:02d}.G",
        f"cryptomatte{rank:02d}.B",
    ]


def estimate_cryptomatte_ranks(object_count: int) -> int:
    """
    Estimate how many cryptomatte ranks are needed for a given object count.

    Each rank can store ~6 objects (2 per pixel in RGBA).
    """
    # Cryptomatte stores 2 IDs per pixel in RG and BA
    # With 3 channels (RGB), we get 2 IDs per rank
    # Conservative estimate
    return math.ceil(object_count / 2)


# ==================== Manifest Merging ====================

def merge_manifests(manifests: List[CryptomatteManifest]) -> CryptomatteManifest:
    """
    Merge multiple manifests into one.
    Useful for combining manifests from different render layers.
    """
    if not manifests:
        return CryptomatteManifest(layer_name="merged")

    merged = CryptomatteManifest(layer_name="merged")
    seen_names: Set[str] = set()

    for manifest in manifests:
        for entry in manifest.entries:
            if entry.name not in seen_names:
                merged.add_entry(entry.name, entry.hash, entry.rank)
                seen_names.add(entry.name)

    return merged
