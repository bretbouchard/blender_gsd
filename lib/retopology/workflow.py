"""
Complete retopology workflow.

Orchestrates the full retopology pipeline from analysis to final game-ready output.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Any, Dict

from .types import RetopologyTarget, RetopologyConfig, RetopologyResult, retopologize
from .decimate import planar_decimate, apply_decimate, DecimateConfig, DecimateMode
from .game_ready import (
    prepare_game_ready,
    GameReadyConfig,
    GameReadyResult,
)


@dataclass
class RetopologyWorkflowResult:
    """
    Complete result of retopology workflow.

    Attributes:
        success: Whether workflow succeeded
        retopology: Retopology result
        game_ready: Game-ready preparation result
        final_mesh: Final output mesh
        errors: List of error messages
        warnings: List of warning messages
    """
    success: bool = False
    retopology: Optional[RetopologyResult] = None
    game_ready: Optional[GameReadyResult] = None
    final_mesh: Any = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class RetopologyWorkflow:
    """
    Complete workflow for game-ready mesh creation.

    Orchestrates analysis, retopology, and game-ready preparation.

    Example:
        >>> workflow = RetopologyWorkflow(target=RetopologyTarget.CURRENT_GEN)
        >>> workflow.set_source(high_poly_mesh)
        >>> workflow.analyze()
        >>> workflow.retopologize()
        >>> workflow.prepare_game_ready()
        >>> result = workflow.finalize()
    """

    def __init__(self, target: RetopologyTarget = RetopologyTarget.DESKTOP):
        self.target = target
        self.source_object: Any = None
        self._retopology_result: Optional[RetopologyResult] = None
        self._game_ready_result: Optional[GameReadyResult] = None

    def set_source(self, source_object: Any) -> 'RetopologyWorkflow':
        """Set source high-poly mesh."""
        self.source_object = source_object
        return self

    def analyze(self) -> Dict[str, Any]:
        """Analyze source mesh for retopology planning."""
        if self.source_object is None:
            return {'error': 'No source object set'}

        try:
            mesh = self.source_object.data

            analysis = {
                'poly_count': len(mesh.polygons),
                'vertex_count': len(mesh.vertices),
                'edge_count': len(mesh.edges),
                'has_uv': len(mesh.uv_layers) > 0,
                'material_count': len(mesh.materials),
            }

            # Check for common issues
            import bmesh
            bm = bmesh.new()
            bm.from_mesh(mesh)

            non_manifold = sum(1 for e in bm.edges if not e.is_manifold)
            ngons = sum(1 for f in bm.faces if len(f.verts) > 4)
            poles = sum(1 for v in bm.verts if len(v.link_edges) > 5)

            bm.free()

            analysis['non_manifold_edges'] = non_manifold
            analysis['ngons'] = ngons
            analysis['poles'] = poles

            return analysis

        except Exception as e:
            return {'error': str(e)}

    def retopologize(self, config: Optional[RetopologyConfig] = None) -> RetopologyWorkflow:
        """Execute retopology."""
        if config is None:
            config = RetopologyConfig(target_poly_count=self._get_target_poly_count())

        self._retopology_result = retopologize(self.source_object, config)
        return self

    def prepare_game_ready(self, config: Optional[GameReadyConfig] = None) -> RetopologyWorkflow:
        """Prepare game-ready output."""
        if self._retopology_result is None or not self._retopology_result.success:
            self.warnings.append("Retopology not complete")
            return self

        if config is None:
            config = GameReadyConfig(target=self.target)

        if self._retopology_result.result_object:
            self._game_ready_result = prepare_game_ready(
                self._retopology_result.result_object,
                config,
            )
        return self

    def finalize(self) -> RetopologyWorkflowResult:
        """Finalize and return result."""
        result = RetopologyWorkflowResult()

        if self._game_ready_result and self._game_ready_result.success:
            result.success = True
            result.retopology = self._retopology_result
            result.game_ready = self._game_ready_result
            result.final_mesh = self._retopology_result.result_object

        return result

    def _get_target_poly_count(self) -> int:
        """Get target poly count for current platform."""
        from .types import get_poly_budget_for_target
        budget = get_poly_budget_for_target(self.target)
        return budget['recommended']


def create_game_ready_mesh(
    source_object: Any,
    target: RetopologyTarget = RetopologyTarget.DESKTOP,
    target_poly_count: Optional[int] = None,
) -> RetopologyWorkflowResult:
    """
    Convenience function for complete game-ready mesh creation.

    Args:
        source_object: High-poly source mesh
        target: Target platform
        target_poly_count: Optional explicit poly count (uses platform default)

    Returns:
        RetopologyWorkflowResult with final mesh
    """
    workflow = RetopologyWorkflow(target=target)
    workflow.set_source(source_object)

    # Analy first
    analysis = workflow.analyze()

    # Configure retopology
    config = RetopologyConfig(
        target_poly_count=target_poly_count or workflow._get_target_poly_count(),
    )

    # Execute retopology
    workflow.retopologize(config)

    # Prepare game-ready
    workflow.prepare_game_ready()

    # Finalize
    return workflow.finalize()
