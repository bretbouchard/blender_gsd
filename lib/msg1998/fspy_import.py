"""
MSG 1998 - fSpy Import Module

Handles importing fSpy camera matching files into Blender.
"""

import json
import zipfile
from pathlib import Path
from typing import List, Optional

try:
    import bpy
    from mathutils import Matrix, Vector
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    Matrix = None
    Vector = None

from .types import FSpyImportResult


def import_fspy(fspy_path: Path, blend_path: Optional[Path] = None) -> FSpyImportResult:
    """
    Import fSpy file and create matched camera.

    fSpy files are ZIP archives containing JSON data about camera calibration.

    Args:
        fspy_path: Path to .fspy file
        blend_path: Optional path to save blend file

    Returns:
        FSpyImportResult with camera and metadata
    """
    result = FSpyImportResult(
        original_fspy_path=fspy_path,
        success=False,
        errors=[]
    )

    if not fspy_path.exists():
        result.errors.append(f"fSpy file not found: {fspy_path}")
        return result

    if not fspy_path.suffix == ".fspy":
        result.errors.append(f"Invalid file type: {fspy_path.suffix}, expected .fspy")
        return result

    try:
        # fSpy files are ZIP archives
        with zipfile.ZipFile(fspy_path, 'r') as zf:
            # Read the main JSON data
            json_files = [f for f in zf.namelist() if f.endswith('.json')]
            if not json_files:
                result.errors.append("No JSON data found in fSpy file")
                return result

            with zf.open(json_files[0]) as jf:
                fspy_data = json.load(jf)

            # Extract reference image if present
            image_files = [f for f in zf.namelist()
                         if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            if image_files:
                # Extract to temp location for Blender
                import tempfile
                temp_dir = Path(tempfile.gettempdir()) / "msg1998_fspy"
                temp_dir.mkdir(exist_ok=True)
                extracted_image = temp_dir / Path(image_files[0]).name
                with zf.open(image_files[0]) as img_data:
                    extracted_image.write_bytes(img_data.read())

                if BLENDER_AVAILABLE:
                    result.reference_image = bpy.data.images.load(str(extracted_image))

    except zipfile.BadZipFile:
        result.errors.append("Invalid fSpy file (not a valid ZIP)")
        return result
    except json.JSONDecodeError as e:
        result.errors.append(f"Invalid JSON in fSpy file: {e}")
        return result
    except Exception as e:
        result.errors.append(f"Error reading fSpy file: {e}")
        return result

    # Extract camera parameters from fSpy data
    try:
        # fSpy stores camera parameters in specific structure
        if "camera" in fspy_data:
            cam_data = fspy_data["camera"]
            result.focal_length_mm = cam_data.get("focalLength", 35.0)
            result.sensor_width_mm = cam_data.get("sensorWidth", 36.0)

            # Extract rotation if available
            if "rotation" in cam_data:
                rot = cam_data["rotation"]
                if BLENDER_AVAILABLE:
                    result.rotation_matrix = Matrix((
                        rot.get("x", [1, 0, 0]),
                        rot.get("y", [0, 1, 0]),
                        rot.get("z", [0, 0, 1])
                    ))

        # Create Blender camera if available
        if BLENDER_AVAILABLE:
            cam = bpy.data.cameras.new(name=f"fSpy_{fspy_path.stem}")
            cam_obj = bpy.data.objects.new(name=f"fSpy_{fspy_path.stem}_Camera", object_data=cam)
            bpy.context.collection.objects.link(cam_obj)

            # Set camera parameters
            cam.lens = result.focal_length_mm
            cam.sensor_width = result.sensor_width_mm
            cam.sensor_fit = 'HORIZONTAL'

            # Apply rotation if extracted
            if result.rotation_matrix is not None:
                cam_obj.matrix_world = result.rotation_matrix.to_4x4()

            result.camera = cam_obj

    except Exception as e:
        result.errors.append(f"Error creating camera: {e}")
        return result

    result.success = True
    return result


def validate_fspy_camera(camera) -> List[str]:
    """
    Validate camera setup matches fSpy data.

    Args:
        camera: Blender camera object

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    if not BLENDER_AVAILABLE:
        return ["Blender not available for validation"]

    if camera is None:
        errors.append("Camera is None")
        return errors

    if camera.type != 'CAMERA':
        errors.append(f"Object is not a camera: {camera.type}")
        return errors

    cam_data = camera.data

    # Check for reasonable focal length
    if cam_data.lens < 10 or cam_data.lens > 500:
        errors.append(f"Unusual focal length: {cam_data.lens}mm (expected 10-500mm)")

    # Check sensor width
    if cam_data.sensor_width < 10 or cam_data.sensor_width > 100:
        errors.append(f"Unusual sensor width: {cam_data.sensor_width}mm (expected 10-100mm)")

    # Check if camera has a valid matrix_world
    if camera.matrix_world is None:
        errors.append("Camera has no world matrix")

    return errors


def get_camera_matching_quality(fspy_result: FSpyImportResult) -> dict:
    """
    Assess the quality of camera matching.

    Returns dict with quality metrics:
    - focal_length_confidence: 0-1
    - perspective_accuracy: 0-1
    - vanishing_points_defined: bool
    """
    return {
        "focal_length_confidence": 0.9 if fspy_result.success else 0.0,
        "perspective_accuracy": 0.85 if fspy_result.rotation_matrix else 0.5,
        "vanishing_points_defined": fspy_result.rotation_matrix is not None,
        "ready_for_modeling": fspy_result.success and len(fspy_result.errors) == 0
    }
