"""MSG 1998 - Batch Export"""
from pathlib import Path
from typing import Dict, List
from .types import ExportJob, OutputSpec

def create_export_jobs(scene_id: str) -> List[ExportJob]:
    """Create export jobs for all shots in scene."""
    return []

def run_export_job(job: ExportJob) -> Path:
    """Execute single export job."""
    return job.composite_path

def batch_export(scene_id: str, formats: List[str]) -> Dict[str, Path]:
    """Export all shots in scene to specified formats."""
    return {}
