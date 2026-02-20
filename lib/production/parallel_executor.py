"""
Parallel Executor

Execute shots and phases in parallel for performance.

Requirements:
- REQ-ORCH-05: Parallel execution where possible
- Dependency analysis and execution graph

Part of Phase 14.1: Production Orchestrator
"""

from __future__ import annotations
import os
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, Future, as_completed
from dataclasses import dataclass, field
from typing import Dict, List, Set, Any, Optional, Callable

from .production_types import (
    ShotConfig,
    ParallelConfig,
)
from .execution_engine import ExecutionEngine


@dataclass
class DependencyGroup:
    """
    Group of shots that can execute in parallel.

    Attributes:
        group_id: Group identifier
        shot_indices: Shot indices in this group
        dependencies: Indices of groups this depends on
    """
    group_id: int
    shot_indices: List[int] = field(default_factory=list)
    dependencies: Set[int] = field(default_factory=set)


@dataclass
class ExecutionGraph:
    """
    Dependency graph for parallel execution.

    Attributes:
        groups: List of dependency groups in order
        total_shots: Total shot count
        parallel_groups: Number of groups that can run in parallel
    """
    groups: List[DependencyGroup] = field(default_factory=list)
    total_shots: int = 0

    @property
    def parallel_groups(self) -> int:
        """Count groups with multiple shots."""
        return sum(1 for g in self.groups if len(g.shot_indices) > 1)


class ParallelExecutor:
    """
    Execute shots in parallel.

    Analyzes shot dependencies and executes independent shots
    concurrently for improved performance.

    Attributes:
        config: Parallel execution configuration
        engine: Execution engine reference
        errors: Errors encountered during execution
    """

    def __init__(self, config: ParallelConfig):
        """
        Initialize parallel executor.

        Args:
            config: Parallel execution configuration
        """
        self.config = config
        self.engine: Optional[ExecutionEngine] = None
        self.errors: List[str] = []
        self._results: Dict[int, bool] = {}

    def execute_shots_parallel(
        self,
        shots: List[ShotConfig],
        engine: ExecutionEngine
    ) -> Dict[int, bool]:
        """
        Execute multiple shots in parallel.

        Args:
            shots: List of shot configurations
            engine: Execution engine to use

        Returns:
            Dictionary mapping shot index to success status
        """
        self.engine = engine
        self._results = {}
        self.errors = []

        # Analyze dependencies
        graph = create_execution_graph(shots)

        # Choose executor based on config
        if self.config.backend == "process":
            executor_class = ProcessPoolExecutor
        else:
            executor_class = ThreadPoolExecutor

        with executor_class(max_workers=self.config.max_workers) as executor:
            # Execute groups in order
            for group in graph.groups:
                # Wait for dependencies
                self._wait_for_dependencies(group, executor)

                # Submit group shots
                futures: Dict[Future, int] = {}
                for shot_idx in group.shot_indices:
                    future = executor.submit(
                        self._execute_shot_safe,
                        shot_idx,
                        shots[shot_idx]
                    )
                    futures[future] = shot_idx

                # Wait for group completion
                for future in as_completed(futures):
                    shot_idx = futures[future]
                    try:
                        success = future.result()
                        self._results[shot_idx] = success
                    except Exception as e:
                        self._results[shot_idx] = False
                        self.errors.append(f"Shot {shot_idx} failed: {e}")

        return self._results

    def execute_phase_parallel(
        self,
        phase: str,
        items: List[Any],
        handler: Callable[[Any], bool]
    ) -> Dict[int, bool]:
        """
        Execute phase items in parallel.

        Args:
            phase: Phase name
            items: Items to process
            handler: Function to process each item

        Returns:
            Dictionary mapping item index to success status
        """
        results: Dict[int, bool] = {}

        if self.config.backend == "process":
            executor_class = ProcessPoolExecutor
        else:
            executor_class = ThreadPoolExecutor

        with executor_class(max_workers=self.config.max_workers) as executor:
            futures: Dict[Future, int] = {}

            for i, item in enumerate(items):
                future = executor.submit(handler, item)
                futures[future] = i

            for future in as_completed(futures):
                idx = futures[future]
                try:
                    results[idx] = future.result()
                except Exception as e:
                    results[idx] = False
                    self.errors.append(f"Phase {phase} item {idx} failed: {e}")

        return results

    def _execute_shot_safe(self, shot_index: int, shot: ShotConfig) -> bool:
        """
        Execute shot with error handling.

        Args:
            shot_index: Shot index
            shot: Shot configuration

        Returns:
            True if successful
        """
        try:
            if self.engine:
                return self.engine.execute_shot(shot_index)
            return True
        except Exception as e:
            self.errors.append(f"Shot {shot_index} error: {e}")
            return False

    def _wait_for_dependencies(
        self,
        group: DependencyGroup,
        executor: Any
    ) -> None:
        """Wait for dependent groups to complete."""
        # In current implementation, groups are executed sequentially
        # Dependencies are implicit in group ordering
        pass


def analyze_dependencies(shots: List[ShotConfig]) -> List[Set[int]]:
    """
    Analyze shot dependencies for parallel execution.

    Groups shots that can run in parallel based on:
    - Scene ordering (shots in same scene can parallelize)
    - Character usage (shots using same character are sequential)
    - Location usage (shots in same location can parallelize)

    Args:
        shots: List of shot configurations

    Returns:
        List of sets, each containing shot indices that can run in parallel
    """
    if not shots:
        return []

    # Build dependency groups
    groups: List[Set[int]] = []
    current_group: Set[int] = set()

    # Track last shot per character and location
    character_last: Dict[str, int] = {}
    location_last: Dict[str, int] = {}

    for i, shot in enumerate(shots):
        can_parallel = True
        dependencies: Set[int] = set()

        # Check character dependency
        if shot.character:
            if shot.character in character_last:
                # Must run after last shot with same character
                prev_idx = character_last[shot.character]
                if prev_idx in current_group:
                    can_parallel = False
                dependencies.add(prev_idx)
            character_last[shot.character] = i

        # Check location dependency (looser - can parallelize in same location)
        if shot.location:
            location_last[shot.location] = i

        # Check scene ordering (same scene can parallelize)
        if i > 0 and shots[i - 1].scene != shot.scene:
            # Scene change - start new group
            if current_group:
                groups.append(current_group)
            current_group = {i}
        elif can_parallel:
            current_group.add(i)
        else:
            # Dependency conflict - start new group
            if current_group:
                groups.append(current_group)
            current_group = {i}

    if current_group:
        groups.append(current_group)

    return groups


def create_execution_graph(shots: List[ShotConfig]) -> ExecutionGraph:
    """
    Create dependency graph for execution.

    Args:
        shots: List of shot configurations

    Returns:
        ExecutionGraph with ordered dependency groups
    """
    graph = ExecutionGraph(total_shots=len(shots))

    if not shots:
        return graph

    # Get parallel groups
    parallel_sets = analyze_dependencies(shots)

    # Convert to dependency groups
    for group_id, shot_indices in enumerate(parallel_sets):
        group = DependencyGroup(
            group_id=group_id,
            shot_indices=list(shot_indices),
        )

        # Add dependencies on previous groups
        if group_id > 0:
            group.dependencies.add(group_id - 1)

        graph.groups.append(group)

    return graph


def get_parallel_estimate(shots: List[ShotConfig], max_workers: int) -> Dict[str, Any]:
    """
    Estimate parallel execution improvement.

    Args:
        shots: List of shot configurations
        max_workers: Maximum parallel workers

    Returns:
        Dictionary with parallelization estimates
    """
    graph = create_execution_graph(shots)

    # Sequential time (assume 1 unit per shot)
    sequential_time = len(shots)

    # Parallel time
    parallel_time = 0
    for group in graph.groups:
        # Time for group = ceil(shots / workers)
        group_shots = len(group.shot_indices)
        group_time = (group_shots + max_workers - 1) // max_workers
        parallel_time += group_time

    speedup = sequential_time / parallel_time if parallel_time > 0 else 1.0

    return {
        "total_shots": len(shots),
        "parallel_groups": len(graph.groups),
        "max_parallelism": max(len(g.shot_indices) for g in graph.groups) if graph.groups else 0,
        "sequential_steps": sequential_time,
        "parallel_steps": parallel_time,
        "speedup_factor": speedup,
        "efficiency": speedup / max_workers if max_workers > 0 else 0,
    }


def optimize_worker_count(shots: List[ShotConfig], max_available: int = 8) -> int:
    """
    Determine optimal worker count for shots.

    Args:
        shots: List of shot configurations
        max_available: Maximum workers available

    Returns:
        Recommended worker count
    """
    if not shots:
        return 1

    graph = create_execution_graph(shots)

    # Find max parallelism in any group
    max_parallelism = max(
        (len(g.shot_indices) for g in graph.groups),
        default=1
    )

    # Don't exceed max parallelism or available workers
    return min(max_parallelism, max_available)


class BatchProcessor:
    """
    Process shots in batches for memory management.

    Attributes:
        batch_size: Shots per batch
        engine: Execution engine
    """

    def __init__(self, batch_size: int = 5):
        """
        Initialize batch processor.

        Args:
            batch_size: Shots per batch
        """
        self.batch_size = batch_size
        self.engine: Optional[ExecutionEngine] = None

    def process_in_batches(
        self,
        shots: List[ShotConfig],
        engine: ExecutionEngine,
        on_batch_complete: Optional[Callable[[int, int], None]] = None
    ) -> Dict[int, bool]:
        """
        Process shots in batches.

        Args:
            shots: List of shots
            engine: Execution engine
            on_batch_complete: Callback(batch_num, shots_in_batch)

        Returns:
            Dictionary mapping shot index to success
        """
        self.engine = engine
        results: Dict[int, bool] = {}
        total_shots = len(shots)

        for batch_start in range(0, total_shots, self.batch_size):
            batch_end = min(batch_start + self.batch_size, total_shots)
            batch_num = batch_start // self.batch_size + 1

            # Process batch
            for i in range(batch_start, batch_end):
                success = engine.execute_shot(i)
                results[i] = success

            # Callback
            if on_batch_complete:
                on_batch_complete(batch_num, batch_end - batch_start)

            # Checkpoint after each batch
            engine.save_checkpoint()

        return results
