"""
MSG 1998 - Location Asset Management

Create and manage location assets.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .types import LocationAsset, LocationBuildState, ModelingStage


def create_location_asset(
    location_id: str,
    source_dir: Path,
    dest_dir: Path
) -> Optional[LocationAsset]:
    """
    Create complete location asset from source materials.

    Args:
        location_id: Location identifier
        source_dir: Source directory with references/fspy
        dest_dir: Destination for blend file

    Returns:
        LocationAsset or None if failed
    """
    if not source_dir.exists():
        return None

    # Create destination
    loc_dest = dest_dir / location_id
    loc_dest.mkdir(parents=True, exist_ok=True)

    # Find references
    references = []
    ref_dir = source_dir / "references"
    if ref_dir.exists():
        for ext in ['.jpg', '.jpeg', '.png', '.tiff']:
            references.extend(ref_dir.glob(f"*{ext}"))

    # Find fSpy files
    fspy_files = []
    fspy_dir = source_dir / "fspy"
    if fspy_dir.exists():
        fspy_files = list(fspy_dir.glob("*.fspy"))

    # Read metadata if exists
    metadata = {}
    asset_json = source_dir / "asset.json"
    if asset_json.exists():
        try:
            with open(asset_json) as f:
                metadata = json.load(f)
        except json.JSONDecodeError:
            pass

    # Read period notes
    period_notes = ""
    notes_path = source_dir / "period_notes.md"
    if notes_path.exists():
        period_notes = notes_path.read_text()

    return LocationAsset(
        location_id=location_id,
        name=metadata.get("name", location_id),
        address=metadata.get("address", ""),
        coordinates=tuple(metadata.get("coordinates", [0.0, 0.0])),
        period_year=metadata.get("period_year", 1998),
        source_dir=source_dir,
        references=references,
        fspy_files=fspy_files,
        period_notes=period_notes
    )


def export_location_package(
    asset: LocationAsset,
    output_dir: Path,
    include_renders: bool = True
) -> Path:
    """
    Export location package for compositing phase.

    Structure:
    output_dir/{LOCATION_ID}/
    ├── {LOCATION_ID}.blend
    ├── metadata.json
    ├── render_layers/
    │   ├── beauty.exr
    │   ├── depth.exr
    │   └── ...
    └── masks/
        ├── bg_mask.png
        ├── mg_mask.png
        └── fg_mask.png

    Args:
        asset: Location asset to export
        output_dir: Output directory
        include_renders: Include render layer files

    Returns:
        Path to exported package
    """
    export_dir = output_dir / asset.location_id
    export_dir.mkdir(parents=True, exist_ok=True)

    # Create metadata
    metadata = {
        "location_id": asset.location_id,
        "name": asset.name,
        "address": asset.address,
        "coordinates": list(asset.coordinates),
        "period_year": asset.period_year,
        "exported_at": datetime.now().isoformat(),
        "render_layers": ["beauty", "depth", "normal", "object_id"],
        "layers": {
            "background": "Buildings and sky",
            "midground": "Main subject and surroundings",
            "foreground": "Street level details"
        }
    }

    metadata_path = export_dir / "metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    # Create directory structure
    (export_dir / "render_layers").mkdir(exist_ok=True)
    (export_dir / "masks").mkdir(exist_ok=True)

    return export_dir


def get_location_status(asset: LocationAsset) -> Dict[str, Any]:
    """
    Get status of location asset.

    Args:
        asset: Location asset

    Returns:
        Status dict
    """
    return {
        "location_id": asset.location_id,
        "name": asset.name,
        "has_references": len(asset.references) > 0,
        "reference_count": len(asset.references),
        "has_fspy": len(asset.fspy_files) > 0,
        "fspy_count": len(asset.fspy_files),
        "has_period_notes": len(asset.period_notes) > 0,
        "ready_for_building": len(asset.references) > 0 or len(asset.fspy_files) > 0
    }


def validate_location_asset(asset: LocationAsset) -> List[str]:
    """
    Validate location asset has required components.

    Args:
        asset: Location asset to validate

    Returns:
        List of validation errors
    """
    errors = []

    if not asset.location_id:
        errors.append("Location missing ID")

    if not asset.name:
        errors.append("Location missing name")

    if not asset.references and not asset.fspy_files:
        errors.append("Location has no references or fSpy files")

    if asset.period_year > 1998:
        errors.append(f"Period year {asset.period_year} is after target 1998")

    return errors


def list_location_assets(assets_dir: Path) -> List[LocationAsset]:
    """
    List all location assets in directory.

    Args:
        assets_dir: Directory containing location folders

    Returns:
        List of LocationAsset objects
    """
    assets = []

    if not assets_dir.exists():
        return assets

    for loc_dir in assets_dir.iterdir():
        if loc_dir.is_dir():
            asset = create_location_asset(
                location_id=loc_dir.name,
                source_dir=loc_dir,
                dest_dir=assets_dir
            )
            if asset:
                assets.append(asset)

    return assets


def create_location_manifest(
    assets: List[LocationAsset],
    output_path: Path
) -> None:
    """
    Create manifest file for multiple locations.

    Args:
        assets: List of location assets
        output_path: Path to write manifest
    """
    manifest = {
        "version": "1.0",
        "created_at": datetime.now().isoformat(),
        "location_count": len(assets),
        "locations": []
    }

    for asset in assets:
        manifest["locations"].append({
            "id": asset.location_id,
            "name": asset.name,
            "address": asset.address,
            "period_year": asset.period_year,
            "coordinates": list(asset.coordinates),
            "reference_count": len(asset.references),
            "fspy_count": len(asset.fspy_files)
        })

    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)


def create_blend_file(
    asset: LocationAsset,
    output_path: Path,
    template_path: Optional[Path] = None
) -> bool:
    """
    Create blend file for location.

    Args:
        asset: Location asset
        output_path: Path for new blend file
        template_path: Optional template blend file

    Returns:
        Success status
    """
    try:
        import bpy
    except ImportError:
        return False

    # If template exists, copy it
    if template_path and template_path.exists():
        import shutil
        shutil.copy(template_path, output_path)
        bpy.ops.wm.open_mainfile(filepath=str(output_path))
    else:
        bpy.ops.wm.read_homefile()

    # Set up scene for location
    scene = bpy.context.scene
    scene.name = asset.location_id

    # Add metadata as scene properties
    scene["location_id"] = asset.location_id
    scene["location_name"] = asset.name
    scene["period_year"] = asset.period_year

    # Save
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))

    return True
