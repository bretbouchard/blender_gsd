"""
Batch Processing System

Provides parallel batch processing for shot rendering with checkpoint-based
resume capability, timeout support, and progress tracking.

Key Features:
- ProcessPoolExecutor for parallel execution (subprocess isolation)
- Checkpoint-based resume (skips completed jobs on restart)
- Per-job timeout support
- Progress tracking and status reporting
- Markdown report generation

Usage:
    from lib.cinematic.batch import BatchProcessor, BatchConfig, create_batch_from_directory
    from lib.cinematic.tracking.types import BatchJob

    # Create batch from shot configs
    jobs = create_batch_from_directory("shots/", "output/")

    # Configure and run
    config = BatchConfig(workers=4, max_retries=2)
    processor = BatchProcessor(config)
    result = processor.process_batch(jobs)

    # Generate report
    generate_batch_report(result, "batch_report.md")
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .tracking.types import BatchConfig, BatchJob, BatchResult


class BatchCheckpoint:
    """
    Checkpoint persistence for batch processing.

    Saves/loads batch state to enable resume on failure.
    Uses JSON for cross-platform compatibility.
    """

    def __init__(self, checkpoint_path: str):
        """
        Initialize checkpoint manager.

        Args:
            checkpoint_path: Path to checkpoint file
        """
        self.checkpoint_path = Path(checkpoint_path)
        self._data: Dict[str, Any] = {"jobs": {}, "started_at": None}

    def load(self) -> Dict[str, Any]:
        """
        Load checkpoint from disk.

        Returns:
            Checkpoint data dict with job statuses
        """
        if self.checkpoint_path.exists():
            try:
                with open(self.checkpoint_path, "r") as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._data = {"jobs": {}, "started_at": None}
        return self._data

    def save(self, data: Dict[str, Any]) -> None:
        """
        Save checkpoint to disk.

        Args:
            data: Checkpoint data to save
        """
        self._data = data
        self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.checkpoint_path, "w") as f:
            json.dump(data, f, indent=2)

    def get_completed_jobs(self) -> List[str]:
        """
        Get list of completed job IDs from checkpoint.

        Returns:
            List of job IDs that completed successfully
        """
        data = self.load()
        return [
            job_id
            for job_id, job_data in data.get("jobs", {}).items()
            if job_data.get("status") == "completed"
        ]

    def mark_job_status(
        self, job_id: str, status: str, error: Optional[str] = None
    ) -> None:
        """
        Update job status in checkpoint.

        Args:
            job_id: Job identifier
            status: New status (pending, running, completed, failed)
            error: Error message if failed
        """
        data = self.load()
        data["jobs"][job_id] = {
            "status": status,
            "error": error,
            "updated_at": datetime.utcnow().isoformat(),
        }
        self.save(data)

    def clear(self) -> None:
        """Clear checkpoint file."""
        if self.checkpoint_path.exists():
            self.checkpoint_path.unlink()
        self._data = {"jobs": {}, "started_at": None}


def run_job_subprocess(
    job: BatchJob, blender_path: str = "blender", timeout: int = 0
) -> BatchJob:
    """
    Execute a single batch job in a subprocess.

    Runs Blender in background mode with the shot config.
    This provides process isolation - a crash in one job
    doesn't affect other jobs.

    Args:
        job: BatchJob to execute
        blender_path: Path to Blender executable
        timeout: Job timeout in seconds (0 = no timeout)

    Returns:
        Updated BatchJob with results
    """
    job.start_time = datetime.utcnow().isoformat()
    job.status = "running"

    try:
        # Build Blender command
        # Assumes shot_config is a YAML file that can be processed
        # by the shot assembly system
        cmd = [
            blender_path,
            "--background",
            "--python-expr",
            f"""
import sys
sys.path.insert(0, '{str(Path(__file__).parent.parent.parent)}')
from lib.cinematic.shot import assemble_shot, render_shot
from lib.cinematic.tracking.types import BatchJob

# Load and render shot
result = assemble_shot('{job.shot_config}')
if result:
    render_shot(output_path='{job.output_path}')
    print("JOB_COMPLETE")
else:
    print("JOB_FAILED: Could not assemble shot")
    sys.exit(1)
""",
        ]

        # Run with optional timeout
        if timeout > 0:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(Path(job.shot_config).parent),
            )
        else:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(Path(job.shot_config).parent),
            )

        # Check result
        if result.returncode == 0 and "JOB_COMPLETE" in result.stdout:
            job.status = "completed"
        else:
            job.status = "failed"
            error_msg = result.stderr or result.stdout or "Unknown error"
            job.error = error_msg[-500:] if len(error_msg) > 500 else error_msg

    except subprocess.TimeoutExpired:
        job.status = "failed"
        job.error = f"Job timed out after {timeout} seconds"

    except subprocess.CalledProcessError as e:
        job.status = "failed"
        job.error = str(e)

    except Exception as e:
        job.status = "failed"
        job.error = f"Unexpected error: {type(e).__name__}: {e}"

    job.end_time = datetime.utcnow().isoformat()
    return job


class BatchProcessor:
    """
    Parallel batch processor with checkpoint resume.

    Uses ProcessPoolExecutor for parallel execution with
    subprocess isolation. Supports resume from checkpoint
    on failure.

    Example:
        config = BatchConfig(workers=4, resume_on_failure=True)
        processor = BatchProcessor(config)

        jobs = [
            BatchJob(name="shot_01", shot_config="shots/shot_01.yaml", output_path="output/"),
            BatchJob(name="shot_02", shot_config="shots/shot_02.yaml", output_path="output/"),
        ]

        result = processor.process_batch(jobs)
        print(f"Completed: {result.completed}/{result.total_jobs}")
    """

    def __init__(
        self,
        config: Optional[BatchConfig] = None,
        job_runner: Optional[Callable[[BatchJob], BatchJob]] = None,
    ):
        """
        Initialize batch processor.

        Args:
            config: Batch processing configuration
            job_runner: Custom job runner function (for testing)
        """
        self.config = config or BatchConfig()
        self._job_runner = job_runner or self._default_job_runner
        self._cancelled = False
        self._checkpoint = BatchCheckpoint(self.config.checkpoint_path)

        # Determine worker count
        if self.config.workers <= 0:
            # Auto-detect: CPU count - 1, minimum 1
            cpu_count = os.cpu_count() or 4
            self._workers = max(1, cpu_count - 1)
        else:
            self._workers = self.config.workers

    def _default_job_runner(self, job: BatchJob) -> BatchJob:
        """Default job runner using subprocess."""
        return run_job_subprocess(
            job,
            blender_path="blender",
            timeout=self.config.timeout_seconds,
        )

    def process_batch(self, jobs: List[BatchJob]) -> BatchResult:
        """
        Process a batch of jobs with parallel execution.

        Args:
            jobs: List of BatchJob objects to process

        Returns:
            BatchResult with completion statistics
        """
        start_time = time.time()
        result = BatchResult(total_jobs=len(jobs))

        # Load checkpoint for resume
        completed_ids = set()
        if self.config.resume_on_failure:
            completed_ids = set(self._checkpoint.get_completed_jobs())

        # Filter out already completed jobs
        pending_jobs = []
        for job in jobs:
            if job.id in completed_ids:
                job.status = "skipped"
                result.skipped += 1
                result.jobs.append(job)
            else:
                pending_jobs.append(job)

        # Process jobs in parallel
        if pending_jobs:
            with ProcessPoolExecutor(max_workers=self._workers) as executor:
                # Submit all jobs
                future_to_job = {
                    executor.submit(self._run_with_retry, job): job
                    for job in pending_jobs
                }

                # Collect results as they complete
                for future in as_completed(future_to_job):
                    if self._cancelled:
                        executor.shutdown(wait=False, cancel_futures=True)
                        break

                    job = future_to_job[future]
                    try:
                        completed_job = future.result()
                        result.jobs.append(completed_job)

                        if completed_job.status == "completed":
                            result.completed += 1
                            self._checkpoint.mark_job_status(
                                completed_job.id, "completed"
                            )
                        else:
                            result.failed += 1
                            if not self.config.continue_on_error:
                                self._cancelled = True

                    except Exception as e:
                        job.status = "failed"
                        job.error = str(e)
                        result.jobs.append(job)
                        result.failed += 1

                        if not self.config.continue_on_error:
                            self._cancelled = True

        # Calculate duration
        result.duration_seconds = time.time() - start_time

        # Clear checkpoint on successful completion
        if result.failed == 0:
            self._checkpoint.clear()

        return result

    def _run_with_retry(self, job: BatchJob) -> BatchJob:
        """Run job with retry support."""
        attempts = 0
        max_attempts = self.config.max_retries + 1

        while attempts < max_attempts:
            attempts += 1
            job.retry_count = attempts - 1

            try:
                result = self._job_runner(job)
                if result.status == "completed":
                    return result

                # Retry on failure if attempts remaining
                if attempts < max_attempts:
                    self._checkpoint.mark_job_status(
                        job.id, "retrying", error=result.error
                    )
                    time.sleep(1)  # Brief delay before retry

            except Exception as e:
                job.status = "failed"
                job.error = f"{type(e).__name__}: {e}"

                if attempts < max_attempts:
                    time.sleep(1)

        return job

    def get_progress(self, jobs: List[BatchJob]) -> Dict[str, Any]:
        """
        Get current progress of batch processing.

        Args:
            jobs: List of all jobs in batch

        Returns:
            Progress dict with counts and percentage
        """
        status_counts = {
            "pending": 0,
            "running": 0,
            "completed": 0,
            "failed": 0,
            "skipped": 0,
        }

        for job in jobs:
            status_counts[job.status] = status_counts.get(job.status, 0) + 1

        total = len(jobs)
        done = status_counts["completed"] + status_counts["failed"] + status_counts["skipped"]
        percentage = (done / total * 100) if total > 0 else 0

        return {
            "total": total,
            "done": done,
            "pending": status_counts["pending"],
            "running": status_counts["running"],
            "completed": status_counts["completed"],
            "failed": status_counts["failed"],
            "skipped": status_counts["skipped"],
            "percentage": round(percentage, 1),
        }

    def cancel(self) -> None:
        """Cancel batch processing."""
        self._cancelled = True

    def clear_checkpoint(self) -> None:
        """Clear checkpoint file (start fresh)."""
        self._checkpoint.clear()


def create_batch_from_directory(
    shot_dir: str,
    output_dir: str,
    pattern: str = "*.yaml",
) -> List[BatchJob]:
    """
    Create batch jobs from shot configuration files in a directory.

    Args:
        shot_dir: Directory containing shot YAML files
        output_dir: Base output directory for all jobs
        pattern: Glob pattern for shot files (default: *.yaml)

    Returns:
        List of BatchJob objects

    Example:
        jobs = create_batch_from_directory("shots/", "renders/")
        # Creates one job per YAML file in shots/
    """
    shot_path = Path(shot_dir)
    output_path = Path(output_dir)

    jobs = []
    for shot_file in sorted(shot_path.glob(pattern)):
        # Derive job name from filename
        job_name = shot_file.stem

        # Create job with shot-specific output directory
        job = BatchJob(
            name=job_name,
            shot_config=str(shot_file),
            output_path=str(output_path / job_name),
        )
        jobs.append(job)

    return jobs


def generate_batch_report(
    result: BatchResult,
    output_path: str,
    include_job_details: bool = True,
) -> str:
    """
    Generate a markdown report for batch processing results.

    Args:
        result: BatchResult from process_batch()
        output_path: Path to write markdown file
        include_job_details: Include per-job details table

    Returns:
        Path to generated report

    Example:
        result = processor.process_batch(jobs)
        report_path = generate_batch_report(result, "batch_report.md")
    """
    lines = [
        "# Batch Processing Report",
        "",
        f"**Generated:** {datetime.utcnow().isoformat()}",
        f"**Duration:** {result.duration_seconds:.2f} seconds",
        "",
        "## Summary",
        "",
        f"| Metric | Count |",
        f"|--------|-------|",
        f"| Total Jobs | {result.total_jobs} |",
        f"| Completed | {result.completed} |",
        f"| Failed | {result.failed} |",
        f"| Skipped | {result.skipped} |",
        "",
    ]

    # Success rate
    if result.total_jobs > 0:
        success_rate = result.completed / result.total_jobs * 100
        lines.extend(
            [
                f"**Success Rate:** {success_rate:.1f}%",
                "",
            ]
        )

    # Job details
    if include_job_details and result.jobs:
        lines.extend(
            [
                "## Job Details",
                "",
                "| Job | Status | Duration | Error |",
                "|-----|--------|----------|-------|",
            ]
        )

        for job in result.jobs:
            # Calculate duration
            duration = ""
            if job.start_time and job.end_time:
                try:
                    start = datetime.fromisoformat(job.start_time)
                    end = datetime.fromisoformat(job.end_time)
                    duration = f"{(end - start).total_seconds():.1f}s"
                except ValueError:
                    pass

            # Truncate error for table
            error = ""
            if job.error:
                error = job.error[:50] + "..." if len(job.error) > 50 else job.error

            lines.append(f"| {job.name} | {job.status} | {duration} | {error} |")

        lines.append("")

    # Failed jobs section
    failed_jobs = [j for j in result.jobs if j.status == "failed"]
    if failed_jobs:
        lines.extend(
            [
                "## Failed Jobs",
                "",
            ]
        )

        for job in failed_jobs:
            lines.extend(
                [
                    f"### {job.name}",
                    "",
                    f"- **ID:** {job.id}",
                    f"- **Config:** {job.shot_config}",
                    f"- **Retries:** {job.retry_count}",
                    "",
                    "**Error:**",
                    "```",
                    job.error or "No error message",
                    "```",
                    "",
                ]
            )

    # Write report
    report_path = Path(output_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines))

    return str(report_path)


# Convenience function for CLI usage
def run_batch(
    shot_dir: str,
    output_dir: str,
    workers: int = 0,
    resume: bool = True,
    timeout: int = 0,
) -> BatchResult:
    """
    Run batch processing on a directory of shot configs.

    Convenience function that combines create_batch_from_directory
    and process_batch.

    Args:
        shot_dir: Directory containing shot YAML files
        output_dir: Output directory for renders
        workers: Number of parallel workers (0 = auto)
        resume: Skip completed jobs on restart
        timeout: Job timeout in seconds (0 = no timeout)

    Returns:
        BatchResult with completion statistics
    """
    config = BatchConfig(
        workers=workers,
        resume_on_failure=resume,
        timeout_seconds=timeout,
    )

    processor = BatchProcessor(config)
    jobs = create_batch_from_directory(shot_dir, output_dir)

    return processor.process_batch(jobs)
