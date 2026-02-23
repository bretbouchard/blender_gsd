"""
MSG 1998 - FDX Handoff Receiver

Handles receiving and validating handoff packages from FDX GSD.
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .types import (
    FDXHandoffPackage,
    LocationAsset,
    PeriodViolation,
    PeriodViolationSeverity
)


def receive_handoff(
    handoff_dir: Path,
    dest_dir: Path,
    scene_id: Optional[str] = None
) -> FDXHandoffPackage:
    """
    Receive and validate handoff package from FDX GSD.

    Expected handoff structure:
    handoff/blender/{SCENE_ID}/
    ├── manifest.json
    ├── scene.json
    ├── locations/
    │   └── {LOC_ID}/
    │       ├── asset.json
    │       ├── references/
    │       ├── fspy/
    │       └── period_notes.md
    └── shots/

    Args:
        handoff_dir: Path to handoff package root
        dest_dir: Destination directory for assets
        scene_id: Optional scene ID filter

    Returns:
        FDXHandoffPackage with validated contents
    """
    package = FDXHandoffPackage(
        scene_id=scene_id or "",
        received_at=datetime.now(),
        source_path=handoff_dir,
        valid=True,
        validation_errors=[]
    )

    if not handoff_dir.exists():
        package.valid = False
        package.validation_errors.append(f"Handoff directory not found: {handoff_dir}")
        return package

    # Find scene directories
    if scene_id:
        scene_dirs = [handoff_dir / scene_id]
    else:
        scene_dirs = [d for d in handoff_dir.iterdir() if d.is_dir()]

    for scene_dir in scene_dirs:
        if not scene_dir.exists():
            continue

        # Read manifest
        manifest_path = scene_dir / "manifest.json"
        if manifest_path.exists():
            try:
                with open(manifest_path) as f:
                    package.manifest = json.load(f)
                    if not package.scene_id:
                        package.scene_id = package.manifest.get("scene_id", scene_dir.name)
            except json.JSONDecodeError as e:
                package.validation_errors.append(f"Invalid manifest.json: {e}")

        # Load locations
        locations_dir = scene_dir / "locations"
        if locations_dir.exists():
            for loc_dir in locations_dir.iterdir():
                if loc_dir.is_dir():
                    asset = load_location_asset(loc_dir)
                    if asset:
                        package.locations.append(asset)

                        # Copy to destination
                        if dest_dir:
                            dest_loc_dir = dest_dir / "locations" / loc_dir.name
                            if not dest_loc_dir.exists():
                                shutil.copytree(loc_dir, dest_loc_dir)

    # Validate package
    errors = validate_handoff(package)
    package.validation_errors.extend(errors)
    package.valid = len(errors) == 0

    return package


def load_location_asset(location_dir: Path) -> Optional[LocationAsset]:
    """
    Load location asset from directory.

    Args:
        location_dir: Directory containing location asset

    Returns:
        LocationAsset or None if invalid
    """
    asset_json = location_dir / "asset.json"
    if not asset_json.exists():
        return None

    try:
        with open(asset_json) as f:
            data = json.load(f)
    except json.JSONDecodeError:
        return None

    # Find references
    references = []
    ref_dir = location_dir / "references"
    if ref_dir.exists():
        for ext in ['.jpg', '.jpeg', '.png', '.tiff']:
            references.extend(ref_dir.glob(f"*{ext}"))

    # Find fSpy files
    fspy_files = []
    fspy_dir = location_dir / "fspy"
    if fspy_dir.exists():
        fspy_files = list(fspy_dir.glob("*.fspy"))

    # Read period notes
    period_notes = ""
    notes_path = location_dir / "period_notes.md"
    if notes_path.exists():
        period_notes = notes_path.read_text()

    return LocationAsset(
        location_id=data.get("id", location_dir.name),
        name=data.get("name", location_dir.name),
        address=data.get("address", ""),
        coordinates=tuple(data.get("coordinates", [0.0, 0.0])),
        period_year=data.get("period_year", 1998),
        source_dir=location_dir,
        references=references,
        fspy_files=fspy_files,
        period_notes=period_notes
    )


def validate_handoff(package: FDXHandoffPackage) -> List[str]:
    """
    Validate handoff package has all required files.

    Args:
        package: Package to validate

    Returns:
        List of validation errors
    """
    errors = []

    # Check manifest
    if not package.manifest:
        errors.append("Missing manifest.json")
    else:
        required_manifest_keys = ["scene_id", "created_at", "version"]
        for key in required_manifest_keys:
            if key not in package.manifest:
                errors.append(f"Missing manifest key: {key}")

    # Check locations
    if not package.locations:
        errors.append("No locations in handoff package")
    else:
        for loc in package.locations:
            if not loc.location_id:
                errors.append("Location missing ID")
            if not loc.references and not loc.fspy_files:
                errors.append(f"Location {loc.location_id} has no references or fSpy files")

    # Validate version compatibility
    if package.manifest:
        version = package.manifest.get("version", "0.0.0")
        # Check if version is compatible (major version match)
        try:
            major = int(version.split('.')[0])
            if major < 1:
                errors.append(f"Unsupported handoff version: {version}")
        except (ValueError, IndexError):
            errors.append(f"Invalid version format: {version}")

    return errors


def get_handoff_status(package: FDXHandoffPackage) -> Dict[str, Any]:
    """
    Get status summary of handoff package.

    Args:
        package: Handoff package

    Returns:
        Status dict with counts and validation results
    """
    return {
        "scene_id": package.scene_id,
        "received_at": package.received_at.isoformat(),
        "valid": package.valid,
        "location_count": len(package.locations),
        "total_references": sum(len(loc.references) for loc in package.locations),
        "total_fspy_files": sum(len(loc.fspy_files) for loc in package.locations),
        "validation_errors": package.validation_errors,
        "ready_for_processing": package.valid and len(package.locations) > 0
    }


def update_handoff_status(
    package: FDXHandoffPackage,
    status: str,
    output_dir: Path
) -> None:
    """
    Update handoff status for FDX GSD tracking.

    Status values:
    - received: Acknowledged receipt
    - in_progress: Work started
    - review: Ready for review
    - complete: Approved, integrated
    - revision_needed: Requires changes
    - blocked: Waiting on dependency

    Args:
        package: Handoff package
        status: New status value
        output_dir: Directory to write status file
    """
    status_data = {
        "scene_id": package.scene_id,
        "status": status,
        "updated_at": datetime.now().isoformat(),
        "location_count": len(package.locations),
        "locations": [loc.location_id for loc in package.locations]
    }

    status_path = output_dir / "handoff_status.json"
    with open(status_path, 'w') as f:
        json.dump(status_data, f, indent=2)
