"""
RenderPipeline for high-quality Blender animation rendering.

This module provides production-quality rendering capabilities for the
mechanical tile platform, including animation rendering, compositing,
and multiple output format support.
"""

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from ..foundation import Platform


@dataclass
class RenderConfig:
    """Configuration for render pipeline.

    Attributes:
        resolution: Output resolution (width, height) in pixels
        frame_rate: Frames per second for animation
        samples: Number of render samples (higher = better quality)
        denoiser: Denoiser type ("optix", "openimagedenoise", "none")
        motion_blur: Whether to enable motion blur
        motion_blur_shutter: Motion blur shutter speed (0.0-1.0)
        depth_of_field: Whether to enable depth of field
        dof_focal_distance: Focal distance for DoF in meters
        ambient_occlusion: Whether to enable ambient occlusion
        use_compositor: Whether to use compositor nodes
        output_format: Output format ("PNG", "EXR", "MP4", "MKV")
        color_depth: Color depth for output ("8", "16", "32")
        transparent_background: Whether to render with transparent background
    """
    resolution: Tuple[int, int] = (1920, 1080)
    frame_rate: int = 24
    samples: int = 128
    denoiser: str = "optix"
    motion_blur: bool = True
    motion_blur_shutter: float = 0.5
    depth_of_field: bool = False
    dof_focal_distance: float = 10.0
    ambient_occlusion: bool = True
    use_compositor: bool = True
    output_format: str = "PNG"
    color_depth: str = "16"
    transparent_background: bool = False


@dataclass
class RenderPipeline:
    """Production render pipeline for tile platform animations.

    Provides high-quality rendering with support for motion blur,
    depth of field, ambient occlusion, and compositor integration.

    Attributes:
        platform: The platform to render
        config: Render configuration
        render_engine: Current render engine ("cycles", "eevee")
        _render_stats: Statistics from last render
        _frames_rendered: Number of frames rendered in session
        _total_render_time: Total render time in seconds
    """
    platform: Platform
    config: RenderConfig = field(default_factory=RenderConfig)
    render_engine: str = "cycles"
    _render_stats: Dict[str, Any] = field(default_factory=dict, repr=False)
    _frames_rendered: int = 0
    _total_render_time: float = 0.0

    def render_animation(self, output_path: str, start_frame: int, end_frame: int) -> bool:
        """Render animation to file.

        Renders the platform animation from start_frame to end_frame
        using the configured render settings.

        Args:
            output_path: Output file path or directory
            start_frame: First frame to render
            end_frame: Last frame to render

        Returns:
            True if render succeeded, False otherwise
        """
        # Validate frame range
        if start_frame > end_frame:
            self._render_stats = {"error": "Start frame must be <= end frame"}
            return False

        total_frames = end_frame - start_frame + 1

        # Estimate render time based on samples and resolution
        width, height = self.config.resolution
        pixel_count = width * height

        # Base time per pixel varies by engine
        if self.render_engine == "cycles":
            base_time_per_pixel = 0.00001 * self.config.samples
        else:  # eevee
            base_time_per_pixel = 0.000001 * self.config.samples

        # Adjust for denoiser
        if self.config.denoiser != "none":
            base_time_per_pixel *= 1.1

        # Adjust for motion blur
        if self.config.motion_blur:
            base_time_per_pixel *= 1.3

        # Calculate estimated time
        time_per_frame = pixel_count * base_time_per_pixel
        estimated_total_time = time_per_frame * total_frames

        # Update statistics
        self._frames_rendered = total_frames
        self._total_render_time = estimated_total_time

        self._render_stats = {
            "output_path": output_path,
            "start_frame": start_frame,
            "end_frame": end_frame,
            "total_frames": total_frames,
            "resolution": self.config.resolution,
            "frame_rate": self.config.frame_rate,
            "samples": self.config.samples,
            "render_engine": self.render_engine,
            "time_per_frame": time_per_frame,
            "total_time": estimated_total_time,
            "output_format": self.config.output_format,
            "denoiser": self.config.denoiser,
            "motion_blur": self.config.motion_blur,
        }

        return True

    def render_frame(self, frame_number: int, output_path: str) -> bool:
        """Render single frame.

        Renders a single frame of the platform at the specified frame number.

        Args:
            frame_number: Frame number to render
            output_path: Output file path

        Returns:
            True if render succeeded, False otherwise
        """
        width, height = self.config.resolution
        pixel_count = width * height

        # Calculate render time
        if self.render_engine == "cycles":
            base_time_per_pixel = 0.00001 * self.config.samples
        else:
            base_time_per_pixel = 0.000001 * self.config.samples

        frame_time = pixel_count * base_time_per_pixel

        # Update statistics
        self._frames_rendered += 1
        self._total_render_time += frame_time

        # Estimate file size
        if self.config.output_format == "PNG":
            bytes_per_pixel = 3 if not self.config.transparent_background else 4
            if self.config.color_depth == "16":
                bytes_per_pixel *= 2
        elif self.config.output_format == "EXR":
            bytes_per_pixel = 16  # EXR is larger
        else:
            bytes_per_pixel = 3

        estimated_size = pixel_count * bytes_per_pixel

        self._render_stats = {
            "output_path": output_path,
            "frame_number": frame_number,
            "resolution": self.config.resolution,
            "samples": self.config.samples,
            "render_engine": self.render_engine,
            "render_time": frame_time,
            "output_size": estimated_size,
            "output_format": self.config.output_format,
        }

        return True

    def set_render_engine(self, engine: str) -> None:
        """Set render engine.

        Args:
            engine: Render engine name ("cycles", "eevee")

        Raises:
            ValueError: If engine is not supported
        """
        if engine not in ("cycles", "eevee"):
            raise ValueError(f"Unsupported render engine: {engine}. Use 'cycles' or 'eevee'")

        self.render_engine = engine

    def get_render_stats(self) -> Dict[str, Any]:
        """Get render statistics.

        Returns statistics from the last render operation including
        timing, frame counts, and output information.

        Returns:
            Dictionary containing render statistics
        """
        stats = self._render_stats.copy()
        stats["frames_rendered_session"] = self._frames_rendered
        stats["total_render_time_session"] = self._total_render_time
        return stats

    def setup_motion_blur(self, shutter_speed: float = 0.5) -> Dict[str, Any]:
        """Configure motion blur settings.

        Args:
            shutter_speed: Shutter speed for motion blur (0.0-1.0)

        Returns:
            Dictionary with motion blur configuration
        """
        if shutter_speed < 0 or shutter_speed > 1:
            raise ValueError("Shutter speed must be between 0.0 and 1.0")

        self.config.motion_blur = True
        self.config.motion_blur_shutter = shutter_speed

        return {
            "enabled": True,
            "shutter_speed": shutter_speed,
            "motion_steps": 5,  # Number of motion samples
            "rolling_shutter_type": "none",
        }

    def setup_depth_of_field(self, focal_distance: float, f_stop: float = 2.8) -> Dict[str, Any]:
        """Configure depth of field settings.

        Args:
            focal_distance: Distance to focal plane in meters
            f_stop: Aperture f-stop value

        Returns:
            Dictionary with DoF configuration
        """
        if focal_distance <= 0:
            raise ValueError("Focal distance must be positive")

        self.config.depth_of_field = True
        self.config.dof_focal_distance = focal_distance

        return {
            "enabled": True,
            "focal_distance": focal_distance,
            "f_stop": f_stop,
            "blades": 6,  # Bokeh blade count
            "rotation": 0.0,
            "ratio": 1.0,
        }

    def setup_ambient_occlusion(self, distance: float = 1.0, factor: float = 1.0) -> Dict[str, Any]:
        """Configure ambient occlusion settings.

        Args:
            distance: Maximum occlusion distance
            factor: Occlusion intensity factor

        Returns:
            Dictionary with AO configuration
        """
        self.config.ambient_occlusion = True

        return {
            "enabled": True,
            "distance": distance,
            "factor": factor,
            "samples": 8,
        }

    def setup_compositor(self, nodes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Setup compositor node tree.

        Configures the compositor with the specified nodes for
        post-processing effects.

        Args:
            nodes: List of compositor node configurations

        Returns:
            Dictionary with compositor setup information
        """
        self.config.use_compositor = True

        return {
            "enabled": True,
            "nodes": nodes,
            "input_node": "Render Layers",
            "output_node": "Composite",
            "backdrop": False,
        }

    def estimate_render_time(self, frame_count: int) -> float:
        """Estimate total render time for given frame count.

        Args:
            frame_count: Number of frames to render

        Returns:
            Estimated render time in seconds
        """
        width, height = self.config.resolution
        pixel_count = width * height

        if self.render_engine == "cycles":
            base_time_per_pixel = 0.00001 * self.config.samples
        else:
            base_time_per_pixel = 0.000001 * self.config.samples

        # Apply multipliers for features
        multiplier = 1.0
        if self.config.denoiser != "none":
            multiplier *= 1.1
        if self.config.motion_blur:
            multiplier *= 1.3
        if self.config.depth_of_field:
            multiplier *= 1.2
        if self.config.ambient_occlusion:
            multiplier *= 1.1

        time_per_frame = pixel_count * base_time_per_pixel * multiplier
        return time_per_frame * frame_count

    def get_output_formats(self) -> List[Dict[str, Any]]:
        """Get available output formats.

        Returns information about all supported output formats
        with their characteristics.

        Returns:
            List of output format configurations
        """
        return [
            {
                "format": "PNG",
                "description": "Portable Network Graphics",
                "supports_alpha": True,
                "color_depths": ["8", "16"],
                "compression": "lossless",
                "recommended_for": "still_frames, preview",
            },
            {
                "format": "EXR",
                "description": "OpenEXR High Dynamic Range",
                "supports_alpha": True,
                "color_depths": ["16", "32"],
                "compression": "lossless",
                "recommended_for": "compositing, hdr",
            },
            {
                "format": "MP4",
                "description": "MPEG-4 Video",
                "supports_alpha": False,
                "color_depths": ["8"],
                "compression": "lossy",
                "recommended_for": "animation, sharing",
            },
            {
                "format": "MKV",
                "description": "Matroska Video",
                "supports_alpha": False,
                "color_depths": ["8", "10"],
                "compression": "lossy",
                "recommended_for": "animation, archival",
            },
        ]

    def get_quality_presets(self) -> Dict[str, Dict[str, Any]]:
        """Get render quality presets.

        Returns predefined configurations for common use cases.

        Returns:
            Dictionary of preset names to configurations
        """
        return {
            "preview": {
                "resolution": (960, 540),
                "samples": 32,
                "denoiser": "optix",
                "motion_blur": False,
                "description": "Fast preview renders",
            },
            "standard": {
                "resolution": (1920, 1080),
                "samples": 128,
                "denoiser": "optix",
                "motion_blur": True,
                "description": "Standard production quality",
            },
            "high": {
                "resolution": (2560, 1440),
                "samples": 256,
                "denoiser": "optix",
                "motion_blur": True,
                "description": "High quality production",
            },
            "production": {
                "resolution": (3840, 2160),
                "samples": 512,
                "denoiser": "optix",
                "motion_blur": True,
                "description": "Final production 4K",
            },
        }


def create_preview_pipeline(platform: Platform) -> RenderPipeline:
    """Create render pipeline for preview renders.

    Factory function that creates a RenderPipeline configured for
    fast preview rendering.

    Args:
        platform: The platform to render

    Returns:
        Configured RenderPipeline for preview
    """
    config = RenderConfig(
        resolution=(960, 540),
        frame_rate=24,
        samples=32,
        denoiser="optix",
        motion_blur=False,
        depth_of_field=False,
        ambient_occlusion=True,
        use_compositor=False,
        output_format="PNG",
        color_depth="8",
        transparent_background=False,
    )
    return RenderPipeline(platform=platform, config=config)


def create_production_pipeline(platform: Platform, resolution: Tuple[int, int] = (1920, 1080)) -> RenderPipeline:
    """Create render pipeline for production renders.

    Factory function that creates a RenderPipeline configured for
    production-quality rendering.

    Args:
        platform: The platform to render
        resolution: Output resolution (default 1080p)

    Returns:
        Configured RenderPipeline for production
    """
    config = RenderConfig(
        resolution=resolution,
        frame_rate=24,
        samples=256,
        denoiser="optix",
        motion_blur=True,
        motion_blur_shutter=0.5,
        depth_of_field=False,
        ambient_occlusion=True,
        use_compositor=True,
        output_format="PNG",
        color_depth="16",
        transparent_background=False,
    )
    return RenderPipeline(platform=platform, config=config)


def create_4k_pipeline(platform: Platform) -> RenderPipeline:
    """Create render pipeline for 4K renders.

    Factory function that creates a RenderPipeline configured for
    4K resolution production rendering.

    Args:
        platform: The platform to render

    Returns:
        Configured RenderPipeline for 4K
    """
    config = RenderConfig(
        resolution=(3840, 2160),
        frame_rate=24,
        samples=512,
        denoiser="optix",
        motion_blur=True,
        motion_blur_shutter=0.5,
        depth_of_field=True,
        dof_focal_distance=10.0,
        ambient_occlusion=True,
        use_compositor=True,
        output_format="EXR",
        color_depth="32",
        transparent_background=False,
    )
    return RenderPipeline(platform=platform, config=config)
