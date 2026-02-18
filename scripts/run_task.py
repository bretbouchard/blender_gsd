#!/usr/bin/env python3
"""
Task Runner - Execute GSD tasks headlessly in Blender.

Usage:
    blender -b -P scripts/run_task.py -- tasks/example_artifact.yaml
    blender -b -P scripts/run_task.py -- --task tasks/panel_v1.yaml

This is the main entry point for deterministic artifact generation.
"""

import sys
import pathlib

# Allow running from Blender where cwd can be weird
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lib.gsd_io import load_task, validate_task
from lib.scene_ops import reset_scene, ensure_collection
from lib.exports import export_mesh, render_preview, ensure_render_rig


def main(task_path: str):
    """
    Execute a GSD task file.

    Args:
        task_path: Path to task YAML/JSON file
    """
    # Load and validate task
    task = load_task(ROOT / task_path)
    errors = validate_task(task)
    if errors:
        print(f"[ERROR] Task validation failed:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    task_id = task["task_id"]
    print(f"[GSD] Running task: {task_id}")

    # Reset scene to clean state
    reset_scene()
    collection = ensure_collection("Generated")

    # Import and run the artifact builder
    # The task file should specify which script to use
    script_name = task.get("script", "artifact_example")
    try:
        # Dynamic import of the artifact script
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "artifact_script",
            ROOT / "scripts" / f"{script_name}.py"
        )
        artifact_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(artifact_module)
    except FileNotFoundError:
        print(f"[ERROR] Artifact script not found: scripts/{script_name}.py")
        sys.exit(1)

    # Build the artifact(s)
    result = artifact_module.build_artifact(task, collection)
    print(f"[GSD] Artifact built: {len(result.get('root_objects', []))} object(s)")

    # Handle outputs
    outputs = task.get("outputs", {})

    if "mesh" in outputs:
        filepath = export_mesh(result["root_objects"], outputs["mesh"], ROOT)
        print(f"[GSD] Mesh exported: {filepath}")

    if "preview" in outputs:
        ensure_render_rig()
        filepath = render_preview(result["root_objects"], outputs["preview"], ROOT)
        print(f"[GSD] Preview rendered: {filepath}")

    # Debug visualization
    debug = task.get("debug", {})
    if debug.get("enabled") and debug.get("show_mask"):
        from lib.debug_materials import apply_mask_debug
        for obj in result["root_objects"]:
            apply_mask_debug(obj, attribute=debug["show_mask"])
        print(f"[GSD] Debug material applied: {debug['show_mask']}")

    print(f"[OK] {task_id} complete")


if __name__ == "__main__":
    # Blender passes args after '--'
    argv = sys.argv
    if "--" in argv:
        task_path = argv[argv.index("--") + 1]
    else:
        # Default task for testing
        task_path = "tasks/example_artifact.yaml"

    main(task_path)
