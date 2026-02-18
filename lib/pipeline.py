"""
Pipeline - Linear deterministic stage execution for Blender node systems.

This is the core abstraction that turns Blender into a compiler.
Each stage receives (geometry_socket, context) and returns (geometry_socket, context).

Stage 0 — Normalize   : Convert params to canonical ranges
Stage 1 — Primary     : Base shape, gross dimensions
Stage 2 — Secondary   : Recesses, cutouts, boolean effects
Stage 3 — Detail      : Surface effects (always masked)
Stage 4 — OutputPrep  : Store attributes, finalize geometry
"""

from __future__ import annotations
from typing import Callable, Dict, Any, List, Tuple

StageFn = Callable[[Any, Dict[str, Any]], Tuple[Any, Dict[str, Any]]]


class Pipeline:
    """
    Linear, deterministic pipeline with optional debug breakpoints.

    Usage:
        pipe = Pipeline()
            .add("normalize", stage_normalize)
            .add("primary", stage_primary)
            .add("secondary", stage_secondary)
            .add("detail", stage_detail)
            .add("output", stage_output)

        geo, ctx = pipe.run(input_geometry, context)

    Debug breakpoints:
        Set context["debug"]["stop_after_stage"] = "secondary"
        to stop execution after that stage completes.
    """

    def __init__(self):
        self.stages: List[tuple[str, StageFn]] = []

    def add(self, name: str, fn: StageFn) -> "Pipeline":
        """Add a stage to the pipeline."""
        self.stages.append((name, fn))
        return self

    def run(self, geometry_socket, context: Dict[str, Any]) -> Tuple[Any, Dict[str, Any]]:
        """
        Execute all stages in order.

        Args:
            geometry_socket: Input geometry socket from node group
            context: Dict containing params, debug flags, node references

        Returns:
            Tuple of (final_geometry_socket, updated_context)
        """
        debug = context.get("debug", {})
        stop_after = debug.get("stop_after_stage")

        for name, fn in self.stages:
            geometry_socket, context = fn(geometry_socket, context)

            context.setdefault("_stages_run", []).append(name)
            context["_last_stage"] = name

            # Breakpoint: stop after specified stage
            if stop_after and name == stop_after:
                context["_pipeline_stopped"] = True
                break

        return geometry_socket, context

    def get_stage_names(self) -> List[str]:
        """Return list of stage names in order."""
        return [name for name, _ in self.stages]
