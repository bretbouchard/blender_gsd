"""
GSD IO - Task file loading for Blender GSD.

Tasks are the control plane. Blender is the execution plane.
"""

from __future__ import annotations
import json
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


def load_task(path: str | Path) -> dict:
    """
    Load a task definition from YAML or JSON.

    Args:
        path: Path to task file

    Returns:
        Task definition dict

    Raises:
        RuntimeError: If YAML file but PyYAML not available
    """
    p = Path(path)
    data = p.read_text(encoding="utf-8")

    if p.suffix.lower() in [".yaml", ".yml"]:
        if not yaml:
            raise RuntimeError(
                "PyYAML not available in Blender Python. "
                "Use JSON or vendor yaml module."
            )
        return yaml.safe_load(data)

    return json.loads(data)


def validate_task(task: dict) -> list[str]:
    """
    Validate a task definition.

    Args:
        task: Task dict to validate

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    required = ["task_id", "intent", "parameters"]
    for field in required:
        if field not in task:
            errors.append(f"Missing required field: {field}")

    if "parameters" in task and not isinstance(task["parameters"], dict):
        errors.append("parameters must be a dict")

    if "outputs" in task:
        if not isinstance(task["outputs"], dict):
            errors.append("outputs must be a dict")

    return errors
