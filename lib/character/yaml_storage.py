"""
Wardrobe YAML Storage

Load and save wardrobe data in YAML format.

Requirements:
- REQ-WARD-01: Costume definition and storage
- REQ-WARD-02: Scene-by-scene costume assignment

Part of Phase 10.1: Wardrobe System
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any

from .wardrobe_types import (
    Costume,
    CostumePiece,
    CostumeAssignment,
    CostumeChange,
    WardrobeRegistry,
)


def load_wardrobe_from_yaml(path: str) -> WardrobeRegistry:
    """Load wardrobe registry from YAML file.

    Args:
        path: Path to YAML file

    Returns:
        WardrobeRegistry instance
    """
    try:
        import yaml
    except ImportError:
        raise ImportError("PyYAML is required for YAML support. Install with: pip install pyyaml")

    with open(path, "r") as f:
        data = yaml.safe_load(f) or {}

    return _parse_wardrobe_data(data)


def _parse_wardrobe_data(data: Dict[str, Any]) -> WardrobeRegistry:
    """Parse wardrobe data from dictionary.

    Args:
        data: Dictionary data

    Returns:
        WardrobeRegistry instance
    """
    registry = WardrobeRegistry(
        production_name=data.get("production_name", ""),
    )

    # Parse costumes
    for costume_data in data.get("costumes", []):
        costume = _parse_costume(costume_data)
        registry.add_costume(costume)

    # Parse assignments
    for assignment_data in data.get("assignments", []):
        assignment = CostumeAssignment.from_dict(assignment_data)
        registry.add_assignment(assignment)

    # Parse changes
    for change_data in data.get("changes", []):
        change = CostumeChange.from_dict(change_data)
        registry.add_change(change)

    return registry


def _parse_costume(data: Dict[str, Any]) -> Costume:
    """Parse costume from dictionary.

    Args:
        data: Dictionary data

    Returns:
        Costume instance
    """
    pieces = [_parse_piece(p) for p in data.get("pieces", [])]
    accessories = [_parse_piece(a) for a in data.get("accessories", [])]

    return Costume(
        name=data.get("name", ""),
        character=data.get("character", ""),
        pieces=pieces,
        accessories=accessories,
        colors=data.get("colors", []),
        condition=data.get("condition", "pristine"),
        notes=data.get("notes", ""),
        reference_images=data.get("reference_images", []),
        version=data.get("version", 1),
    )


def _parse_piece(data: Dict[str, Any]) -> CostumePiece:
    """Parse costume piece from dictionary.

    Args:
        data: Dictionary data

    Returns:
        CostumePiece instance
    """
    return CostumePiece.from_dict(data)


def save_wardrobe_to_yaml(registry: WardrobeRegistry, path: str) -> None:
    """Save wardrobe registry to YAML file.

    Args:
        registry: Wardrobe registry
        path: Output file path
    """
    try:
        import yaml
    except ImportError:
        raise ImportError("PyYAML is required for YAML support. Install with: pip install pyyaml")

    data = registry.to_dict()

    # Ensure directory exists
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)

    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def load_character_wardrobe(path: str, character: str) -> Dict[str, Any]:
    """Load wardrobe for a specific character from YAML.

    Args:
        path: Path to character wardrobe YAML file
        character: Character name

    Returns:
        Dictionary with character's wardrobe data
    """
    try:
        import yaml
    except ImportError:
        raise ImportError("PyYAML is required for YAML support")

    with open(path, "r") as f:
        data = yaml.safe_load(f) or {}

    # Extract character-specific data
    result = {
        "character": data.get("character", character),
        "costumes": [],
        "assignments": [],
    }

    # Parse costumes
    for costume_data in data.get("costumes", []):
        costume_data["character"] = result["character"]
        result["costumes"].append(costume_data)

    # Parse assignments
    for assignment_data in data.get("assignments", []):
        assignment_data["character"] = result["character"]
        result["assignments"].append(assignment_data)

    return result


def load_wardrobe_from_directory(directory: str) -> WardrobeRegistry:
    """Load wardrobe from all YAML files in a directory.

    Loads all *.yaml files and merges them into a single registry.

    Args:
        directory: Directory containing YAML files

    Returns:
        WardrobeRegistry instance
    """
    registry = WardrobeRegistry()
    dir_path = Path(directory)

    if not dir_path.exists():
        return registry

    for yaml_file in sorted(dir_path.glob("*.yaml")):
        if yaml_file.name in ("schema.yaml", "template.yaml"):
            continue

        try:
            file_registry = load_wardrobe_from_yaml(str(yaml_file))

            # Merge into main registry
            for costume in file_registry.costumes.values():
                registry.add_costume(costume)

            for assignment in file_registry.assignments:
                registry.add_assignment(assignment)

            for change in file_registry.changes:
                registry.add_change(change)

            # Use first production name if not set
            if not registry.production_name and file_registry.production_name:
                registry.production_name = file_registry.production_name

        except Exception as e:
            print(f"Warning: Failed to load {yaml_file}: {e}")
            continue

    return registry


def validate_yaml_structure(data: Dict[str, Any]) -> List[str]:
    """Validate YAML structure.

    Args:
        data: Parsed YAML data

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Check costumes structure
    if "costumes" in data:
        if not isinstance(data["costumes"], list):
            errors.append("'costumes' must be a list")
        else:
            for i, costume in enumerate(data["costumes"]):
                if not isinstance(costume, dict):
                    errors.append(f"costumes[{i}] must be a dictionary")
                    continue

                if "name" not in costume:
                    errors.append(f"costumes[{i}] missing 'name'")

                if "pieces" in costume and not isinstance(costume["pieces"], list):
                    errors.append(f"costumes[{i}].pieces must be a list")

    # Check assignments structure
    if "assignments" in data:
        if not isinstance(data["assignments"], list):
            errors.append("'assignments' must be a list")
        else:
            for i, assignment in enumerate(data["assignments"]):
                if not isinstance(assignment, dict):
                    errors.append(f"assignments[{i}] must be a dictionary")
                    continue

                for required in ["scene", "costume"]:
                    if required not in assignment:
                        errors.append(f"assignments[{i}] missing '{required}'")

    # Check changes structure
    if "changes" in data:
        if not isinstance(data["changes"], list):
            errors.append("'changes' must be a list")

    return errors


# Default file extension for wardrobe files
WARDROBE_FILE_EXTENSION = ".yaml"


def find_wardrobe_files(directory: str) -> List[str]:
    """Find all wardrobe YAML files in a directory.

    Args:
        directory: Directory to search

    Returns:
        List of file paths
    """
    dir_path = Path(directory)
    if not dir_path.exists():
        return []

    return [
        str(f) for f in dir_path.glob(f"*{WARDROBE_FILE_EXTENSION}")
        if f.name not in ("schema.yaml", "template.yaml")
    ]
