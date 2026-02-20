"""
Execution Engine

Main production execution engine for orchestrating all phases.

Requirements:
- REQ-ORCH-03: Execute all phases in order
- REQ-ORCH-04: Progress tracking and resume
- REQ-ORCH-06: Error handling and rollback

Part of Phase 14.1: Production Orchestrator
"""

from __future__ import annotations
import os
import json
import time
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable

from .production_types import (
    ProductionConfig,
    ProductionResult,
    ExecutionState,
    ExecutionPhase,
    ExecutionStatus,
    ShotConfig,
    EXECUTION_PHASES,
)
from .production_validator import validate_for_execution
from .production_loader import save_yaml


class ExecutionEngine:
    """
    Main production execution engine.

    Orchestrates all phases of production execution with checkpointing
    for resume capability.

    Attributes:
        config: Production configuration
        state: Current execution state
        checkpoint_interval: Shots between checkpoints
        on_progress: Optional progress callback
        on_phase_start: Optional phase start callback
        on_shot_complete: Optional shot complete callback
        on_error: Optional error callback
    """

    def __init__(self, config: ProductionConfig):
        """
        Initialize execution engine.

        Args:
            config: Production configuration
        """
        self.config = config
        self.state = ExecutionState(
            production_id=config.meta.production_id,
            status=ExecutionStatus.PENDING.value,
        )
        self.checkpoint_interval = 10  # shots
        self.start_time: float = 0.0

        # Callbacks
        self.on_progress: Optional[Callable[[Dict[str, Any]], None]] = None
        self.on_phase_start: Optional[Callable[[str], None]] = None
        self.on_shot_complete: Optional[Callable[[int, bool], None]] = None
        self.on_error: Optional[Callable[[str, Exception], None]] = None

        # Phase handlers (can be overridden)
        self._phase_handlers = {
            ExecutionPhase.VALIDATE.value: self._execute_validate,
            ExecutionPhase.PREPARE.value: self._execute_prepare,
            ExecutionPhase.CHARACTERS.value: self._execute_characters,
            ExecutionPhase.LOCATIONS.value: self._execute_locations,
            ExecutionPhase.SHOTS.value: self._execute_shots,
            ExecutionPhase.POST_PROCESS.value: self._execute_post_process,
            ExecutionPhase.EXPORT.value: self._execute_export,
            ExecutionPhase.FINALIZE.value: self._execute_finalize,
        }

        # Shot handlers
        self._shot_renderer: Optional[Callable[[ShotConfig], bool]] = None

    def execute(self) -> ProductionResult:
        """
        Execute entire production.

        Returns:
            ProductionResult with execution outcome
        """
        self.start_time = time.time()
        self.state.status = ExecutionStatus.RUNNING.value
        self.state.started_at = datetime.now().isoformat()
        self.state.touch()

        errors: List[str] = []
        warnings: List[str] = []
        output_paths: List[str] = []

        try:
            # Execute each phase in order
            for phase in EXECUTION_PHASES:
                self.state.current_phase = phase.value
                self._update_progress()

                if self.on_phase_start:
                    self.on_phase_start(phase.value)

                success = self.execute_phase(phase.value)

                if not success:
                    self.state.status = ExecutionStatus.FAILED.value
                    errors.append(f"Phase {phase.value} failed")
                    break

                self.state.advance_phase()

            # Determine success
            if not errors:
                self.state.status = ExecutionStatus.COMPLETED.value
                self.state.progress = 100.0

        except Exception as e:
            self.state.status = ExecutionStatus.FAILED.value
            self.state.error_message = str(e)
            errors.append(f"Execution error: {e}\n{traceback.format_exc()}")

            if self.on_error:
                self.on_error("execute", e)

        finally:
            self.state.touch()
            self.save_checkpoint()

        # Build result
        total_time = time.time() - self.start_time
        result = ProductionResult(
            success=(self.state.status == ExecutionStatus.COMPLETED.value),
            shots_completed=len(self.state.completed_shots),
            shots_failed=len(self.state.failed_shots),
            total_time=total_time,
            output_paths=output_paths,
            errors=errors,
            warnings=warnings,
            state=self.state,
        )

        return result

    def execute_phase(self, phase: str) -> bool:
        """
        Execute single phase.

        Args:
            phase: Phase name

        Returns:
            True if successful
        """
        handler = self._phase_handlers.get(phase)
        if handler:
            return handler()
        return True

    def execute_shot(self, shot_index: int) -> bool:
        """
        Execute single shot.

        Args:
            shot_index: Index of shot in config

        Returns:
            True if successful
        """
        if shot_index >= len(self.config.shots):
            return False

        shot = self.config.shots[shot_index]
        self.state.current_shot = shot_index
        self.state.touch()

        try:
            # Use custom renderer if set
            if self._shot_renderer:
                success = self._shot_renderer(shot)
            else:
                success = self._render_shot(shot)

            if success:
                self.state.complete_shot(shot_index)
            else:
                self.state.fail_shot(shot_index)

            if self.on_shot_complete:
                self.on_shot_complete(shot_index, success)

            # Checkpoint periodically
            if (shot_index + 1) % self.checkpoint_interval == 0:
                self.save_checkpoint()

            return success

        except Exception as e:
            self.state.fail_shot(shot_index)
            self.state.error_message = f"Shot {shot_index} error: {e}"

            if self.on_error:
                self.on_error(f"shot_{shot_index}", e)

            return False

    def save_checkpoint(self) -> None:
        """Save execution state to checkpoint file."""
        if not self.state.checkpoint_path:
            # Create default checkpoint path
            checkpoint_dir = os.path.join(
                self.config.base_path or ".",
                ".gsd-state",
                "production"
            )
            os.makedirs(checkpoint_dir, exist_ok=True)
            self.state.checkpoint_path = os.path.join(
                checkpoint_dir,
                f"{self.state.production_id}_checkpoint.json"
            )

        checkpoint_data = {
            "state": self.state.to_dict(),
            "config_path": getattr(self.config, "_source_path", ""),
            "timestamp": datetime.now().isoformat(),
        }

        with open(self.state.checkpoint_path, "w") as f:
            json.dump(checkpoint_data, f, indent=2)

    def load_checkpoint(self, path: str) -> None:
        """
        Load execution state from checkpoint.

        Args:
            path: Path to checkpoint file
        """
        with open(path, "r") as f:
            checkpoint_data = json.load(f)

        self.state = ExecutionState.from_dict(checkpoint_data["state"])
        self.state.checkpoint_path = path

    def estimate_remaining_time(self) -> float:
        """
        Estimate time remaining in seconds.

        Returns:
            Estimated seconds remaining
        """
        # Calculate shots remaining
        total_shots = len(self.config.shots)
        completed = len(self.state.completed_shots)
        remaining_shots = total_shots - completed

        if remaining_shots <= 0:
            return 0.0

        # Calculate average time per completed shot
        elapsed = time.time() - self.start_time
        if completed > 0:
            avg_time_per_shot = elapsed / completed
        else:
            # Default estimate: 60 seconds per shot
            avg_time_per_shot = 60.0

        # Estimate remaining phases
        remaining_phases = 0
        current_found = False
        for phase in EXECUTION_PHASES:
            if phase.value == self.state.current_phase:
                current_found = True
            elif current_found:
                remaining_phases += 1

        # Phase overhead (5 seconds each)
        phase_overhead = remaining_phases * 5

        return (remaining_shots * avg_time_per_shot) + phase_overhead

    def get_progress(self) -> Dict[str, Any]:
        """
        Get current progress info.

        Returns:
            Dictionary with progress details
        """
        total_shots = len(self.config.shots)
        completed = len(self.state.completed_shots)
        failed = len(self.state.failed_shots)

        return {
            "status": self.state.status,
            "phase": self.state.current_phase,
            "shots_total": total_shots,
            "shots_completed": completed,
            "shots_failed": failed,
            "shots_remaining": total_shots - completed - failed,
            "progress_percent": self.state.progress,
            "elapsed_seconds": time.time() - self.start_time if self.start_time else 0,
            "estimated_remaining": self.estimate_remaining_time(),
            "current_shot_index": self.state.current_shot,
            "production_id": self.state.production_id,
        }

    def pause(self) -> None:
        """Pause execution."""
        self.state.status = ExecutionStatus.PAUSED.value
        self.save_checkpoint()

    def resume(self) -> None:
        """Resume paused execution."""
        if self.state.status == ExecutionStatus.PAUSED.value:
            self.state.status = ExecutionStatus.RUNNING.value
            self.state.touch()

    def cancel(self) -> None:
        """Cancel execution."""
        self.state.status = ExecutionStatus.CANCELLED.value
        self.save_checkpoint()

    def set_shot_renderer(self, renderer: Callable[[ShotConfig], bool]) -> None:
        """
        Set custom shot renderer.

        Args:
            renderer: Function that takes ShotConfig and returns success bool
        """
        self._shot_renderer = renderer

    def _update_progress(self) -> None:
        """Update progress percentage."""
        total_phases = len(EXECUTION_PHASES)
        current_phase_idx = 0

        for i, phase in enumerate(EXECUTION_PHASES):
            if phase.value == self.state.current_phase:
                current_phase_idx = i
                break

        # Calculate base progress from phases
        phase_progress = (current_phase_idx / total_phases) * 100

        # Add shot progress if in shots phase
        if self.state.current_phase == ExecutionPhase.SHOTS.value:
            total_shots = len(self.config.shots)
            if total_shots > 0:
                completed = len(self.state.completed_shots)
                shot_progress = (completed / total_shots) * (100 / total_phases)
                phase_progress = (current_phase_idx / total_phases) * 100 + shot_progress

        self.state.progress = min(phase_progress, 99.9)  # Never show 100% until done

        if self.on_progress:
            self.on_progress(self.get_progress())

    # Phase handlers

    def _execute_validate(self) -> bool:
        """Validate phase - check production configuration."""
        result = validate_for_execution(self.config)

        if not result.valid:
            self.state.error_message = "Validation failed: " + "; ".join(
                e.message for e in result.errors
            )
            return False

        return True

    def _execute_prepare(self) -> bool:
        """Prepare phase - setup assets and scenes."""
        # This would integrate with Blender to:
        # - Load character models
        # - Setup location presets
        # - Prepare render settings

        # For now, just validate paths exist
        if self.config.script_path and not os.path.exists(self.config.script_path):
            # Non-fatal warning
            pass

        return True

    def _execute_characters(self) -> bool:
        """Characters phase - setup characters and costumes."""
        # This would integrate with the wardrobe system to:
        # - Load character models
        # - Apply costumes for each scene
        # - Setup character animation

        for name, char in self.config.characters.items():
            if char.model and not os.path.exists(char.model):
                # Log warning but continue
                pass

        return True

    def _execute_locations(self) -> bool:
        """Locations phase - setup locations."""
        # This would integrate with the set builder to:
        # - Create location sets
        # - Load HDRI environments
        # - Setup props

        return True

    def _execute_shots(self) -> bool:
        """Shots phase - render all shots."""
        total_shots = len(self.config.shots)

        # Resume from checkpoint if needed
        start_index = self.state.current_shot
        if start_index == 0 and self.state.completed_shots:
            start_index = max(self.state.completed_shots) + 1

        for i in range(start_index, total_shots):
            if i in self.state.completed_shots:
                continue

            if self.state.status == ExecutionStatus.CANCELLED.value:
                return False

            if self.state.status == ExecutionStatus.PAUSED.value:
                return False

            success = self.execute_shot(i)
            self._update_progress()

            if not success and i in self.state.failed_shots:
                # Continue with other shots on failure
                pass

        return True

    def _execute_post_process(self) -> bool:
        """Post-process phase - apply effects."""
        # This would integrate with compositor to:
        # - Apply color grading
        # - Add lens effects
        # - Apply retro conversion if needed

        return True

    def _execute_export(self) -> bool:
        """Export phase - export all formats."""
        # This would integrate with render system to:
        # - Export video files
        # - Generate sprite sheets for game assets
        # - Create format variations

        return True

    def _execute_finalize(self) -> bool:
        """Finalize phase - generate reports and manifests."""
        # This would:
        # - Generate render manifest
        # - Create shot report
        # - Archive production state

        return True

    def _render_shot(self, shot: ShotConfig) -> bool:
        """
        Default shot renderer.

        This is a placeholder that would integrate with the
        cinematic system to render shots.

        Args:
            shot: Shot configuration

        Returns:
            True if successful
        """
        # This would:
        # 1. Load shot template
        # 2. Setup camera, lights, backdrop
        # 3. Apply character costume
        # 4. Setup location
        # 5. Render frames

        # Placeholder: just return success
        return True


def execute_production(config: ProductionConfig) -> ProductionResult:
    """
    One-command production execution.

    Args:
        config: Production configuration

    Returns:
        ProductionResult with execution outcome
    """
    engine = ExecutionEngine(config)
    return engine.execute()


def resume_production(checkpoint_path: str, config: ProductionConfig) -> ProductionResult:
    """
    Resume production from checkpoint.

    Args:
        checkpoint_path: Path to checkpoint file
        config: Production configuration

    Returns:
        ProductionResult with execution outcome
    """
    engine = ExecutionEngine(config)
    engine.load_checkpoint(checkpoint_path)

    if engine.state.status not in (ExecutionStatus.PAUSED.value, ExecutionStatus.FAILED.value):
        raise ValueError(f"Cannot resume from status: {engine.state.status}")

    engine.resume()
    return engine.execute()
