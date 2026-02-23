"""MSG 1998 - Output Format Configuration"""
from typing import Dict, Tuple
from .types import OutputSpec

OUTPUT_FORMATS: Dict[str, OutputSpec] = {
    "master_exr": OutputSpec(
        format="OPEN_EXR",
        resolution=(4096, 1716),
        frame_rate=24,
        color_space="ACEScg",
        compression="ZIP",
    ),
    "prores_4444": OutputSpec(
        format="QUICKTIME",
        resolution=(4096, 1716),
        frame_rate=24,
        color_space="Rec709",
        compression="prores_4444",
    ),
    "prores_422": OutputSpec(
        format="QUICKTIME",
        resolution=(2048, 858),
        frame_rate=24,
        color_space="Rec709",
        compression="prores_422",
    ),
    "preview_h264": OutputSpec(
        format="FFMPEG",
        resolution=(1920, 804),
        frame_rate=24,
        color_space="Rec709",
        compression="h264_high",
    ),
}

def configure_output(scene, spec: OutputSpec) -> None:
    """Configure scene output settings."""
    pass
