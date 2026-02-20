"""
Render Pipeline for City Chase Sequences

Provides complete render setup and execution for chase scenes.

Usage:
    from lib.animation.city.render_pipeline import ChaseRenderPipeline

    # Quick render
    pipeline = ChaseRenderPipeline()
    pipeline.quick_render(output_path="//output/chase_")

    # Full production render
    pipeline = ChaseRenderPipeline(
        resolution=(1920, 1080),
        fps=24,
        samples=256
    )
    pipeline.setup_compositor()
    pipeline.render_animation("//output/charlotte_chase_")
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Callable
from pathlib import Path
import bpy
from bpy.types import Scene, Camera, Collection
from mathutils import Vector
import math
import os


@dataclass
class RenderConfig:
    """Render configuration."""
    # Output
    resolution_x: int = 1920
    resolution_y: int = 1080
    fps: int = 24
    frame_start: int = 1
    frame_end: int = 720

    # File
    output_path: str = "//output/"
    file_format: str = "FFMPEG"  # PNG, OPEN_EXR, FFMPEG
    codec: str = "H264"  # For FFMPEG
    container: str = "MPEG4"  # For FFMPEG
    quality: int = 90  # For image formats

    # Render settings
    engine: str = "CYCLES"  # CYCLES, BLENDER_EEVEE
    samples: int = 128
    denoise: bool = True
    motion_blur: bool = True
    motion_blur_shutter: float = 0.5

    # Performance
    use_tiles: bool = False
    tile_x: int = 256
    tile_y: int = 256

    # Compositor
    enable_compositor: bool = True
    color_correction: bool = True
    bloom: bool = False
    glare: bool = False
    vignette: bool = False
    film_grain: bool = False


# Preset configurations
RENDER_PRESETS = {
    "preview": RenderConfig(
        resolution_x=1280,
        resolution_y=720,
        samples=32,
        denoise=False,
        motion_blur=False,
    ),
    "standard": RenderConfig(
        resolution_x=1920,
        resolution_y=1080,
        samples=128,
        denoise=True,
    ),
    "high_quality": RenderConfig(
        resolution_x=1920,
        resolution_y=1080,
        samples=256,
        denoise=True,
        motion_blur=True,
        enable_compositor=True,
        bloom=True,
    ),
    "4k": RenderConfig(
        resolution_x=3840,
        resolution_y=2160,
        samples=256,
        denoise=True,
        motion_blur=True,
    ),
    "production": RenderConfig(
        resolution_x=1920,
        resolution_y=1080,
        samples=512,
        denoise=True,
        motion_blur=True,
        enable_compositor=True,
        color_correction=True,
        glare=True,
        vignette=True,
    ),
}


class ChaseRenderPipeline:
    """
    Complete render pipeline for chase sequences.

    Features:
    - Quick preview renders
    - Production quality setup
    - Compositor effects
    - Multi-camera output
    - Batch rendering
    """

    def __init__(self, config: Optional[RenderConfig] = None):
        self.config = config or RenderConfig()
        self.scene = bpy.context.scene

    @classmethod
    def from_preset(cls, preset: str) -> 'ChaseRenderPipeline':
        """Create pipeline from preset."""
        if preset not in RENDER_PRESETS:
            available = list(RENDER_PRESETS.keys())
            raise ValueError(f"Unknown preset: {preset}. Available: {available}")

        return cls(RENDER_PRESETS[preset])

    def setup_scene(self) -> None:
        """Apply render settings to scene."""
        scene = self.scene

        # Resolution
        scene.render.resolution_x = self.config.resolution_x
        scene.render.resolution_y = self.config.resolution_y
        scene.render.resolution_percentage = 100

        # Frame rate
        scene.render.fps = self.config.fps

        # Frame range
        scene.frame_start = self.config.frame_start
        scene.frame_end = self.config.frame_end

        # Render engine
        scene.render.engine = self.config.engine

        # Cycles settings
        if self.config.engine == "CYCLES":
            scene.cycles.samples = self.config.samples
            scene.cycles.use_denoising = self.config.denoise

            if self.config.motion_blur:
                scene.render.use_motion_blur = True
                scene.render.motion_blur_shutter = self.config.motion_blur_shutter

        # EEVEE settings
        elif self.config.engine == "BLENDER_EEVEE":
            scene.eevee.taa_render_samples = self.config.samples
            scene.eevee.use_motion_blur = self.config.motion_blur

        # Output format
        scene.render.image_settings.file_format = self.config.file_format

        if self.config.file_format == "FFMPEG":
            scene.render.ffmpeg.codec = self.config.codec
            scene.render.ffmpeg.container = self.config.container
            scene.render.ffmpeg.constant_bitrate = 15000  # 15 Mbps

        elif self.config.file_format in ["PNG", "JPEG"]:
            scene.render.image_settings.quality = self.config.quality

        # Tiling (for large renders)
        if self.config.use_tiles:
            scene.render.tile_x = self.config.tile_x
            scene.render.tile_y = self.config.tile_y
        else:
            scene.render.tile_x = self.config.resolution_x
            scene.render.tile_y = self.config.resolution_y

        print(f"Render setup: {self.config.resolution_x}x{self.config.resolution_y} "
              f"@ {self.config.fps}fps, {self.config.samples} samples")

    def setup_compositor(self) -> None:
        """Setup compositor nodes for post-processing."""
        if not self.config.enable_compositor:
            return

        scene = self.scene
        scene.use_nodes = True

        tree = scene.node_tree
        nodes = tree.nodes
        links = tree.links

        # Clear existing nodes
        nodes.clear()

        # Create render layers
        render_layers = nodes.new('CompositorNodeRLayers')
        render_layers.location = (-800, 0)

        # Create output
        output = nodes.new('CompositorNodeComposite')
        output.location = (800, 0)

        # Viewer for preview
        viewer = nodes.new('CompositorNodeViewer')
        viewer.location = (800, -300)

        # Build node chain
        last_node = render_layers

        # Color correction
        if self.config.color_correction:
            color_balance = nodes.new('CompositorNodeColorBalance')
            color_balance.location = (-400, 0)
            color_balance.correction_method = 'OFFSET_POWER_SLOPE'
            # Slightly warm, cinematic look
            color_balance.offset = (0.02, 0.01, 0.0)
            color_balance.power = (1.05, 1.0, 0.95)
            color_balance.slope = (1.1, 1.0, 0.95)
            links.new(last_node.outputs['Image'], color_balance.inputs['Image'])
            last_node = color_balance

        # Glare/Bloom
        if self.config.glare:
            glare = nodes.new('CompositorNodeGlare')
            glare.location = (-200, 100)
            glare.glare_type = 'FOG_GLOW'
            glare.quality = 'MEDIUM'
            glare.threshold = 0.8
            links.new(last_node.outputs['Image'], glare.inputs['Image'])
            last_node = glare

        # Vignette
        if self.config.vignette:
            # Create vignette using lens distortion trick
            vignette = nodes.new('CompositorNodeLensdist')
            vignette.location = (0, 0)
            vignette.use_jitter = False
            vignette.use_fit = True
            # Would need proper vignette math, simplified here
            links.new(last_node.outputs['Image'], vignette.inputs['Image'])
            last_node = vignette

        # Film grain
        if self.config.film_grain:
            # Add subtle noise
            pass  # Complex to implement properly

        # Connect to output
        links.new(last_node.outputs['Image'], output.inputs['Image'])
        links.new(last_node.outputs['Image'], viewer.inputs['Image'])

        print("Compositor setup complete")

    def setup_camera_rig(self, camera: Optional[Camera] = None) -> None:
        """Setup camera with chase-appropriate settings."""
        if camera is None:
            camera = self.scene.camera

        if camera is None:
            return

        cam_data = camera.data

        # Depth of field for cinematic look
        cam_data.dof.use_dof = True
        cam_data.dof.aperture_fstop = 2.8
        cam_data.dof.focus_distance = 20.0  # Will be animated

        # Sensor size for cinematic FOV
        cam_data.sensor_width = 36.0
        cam_data.sensor_height = 24.0

        # Safe areas for action
        cam_data.show_safe_areas = True

    def quick_render(
        self,
        output_path: str = "//output/preview_",
        frame: Optional[int] = None
    ) -> str:
        """
        Quick single-frame render.

        Args:
            output_path: Output file path
            frame: Frame to render (current if None)

        Returns:
            Path to rendered file
        """
        # Save current settings
        original_engine = self.scene.render.engine
        original_samples = self.scene.cycles.samples if original_engine == "CYCLES" else 0

        # Set preview settings
        self.scene.render.engine = "CYCLES"
        self.scene.cycles.samples = 32
        self.scene.render.resolution_percentage = 50

        # Set frame
        if frame is not None:
            self.scene.frame_set(frame)

        # Set output
        self.scene.render.filepath = output_path

        # Render
        bpy.ops.render.render(write_still=True)

        # Restore settings
        self.scene.render.engine = original_engine
        if original_engine == "CYCLES":
            self.scene.cycles.samples = original_samples
        self.scene.render.resolution_percentage = 100

        print(f"Quick render saved to: {output_path}")
        return output_path

    def render_animation(
        self,
        output_path: str = "//output/chase_",
        frame_start: Optional[int] = None,
        frame_end: Optional[int] = None
    ) -> str:
        """
        Render full animation.

        Args:
            output_path: Output file path pattern
            frame_start: Start frame (scene setting if None)
            frame_end: End frame (scene setting if None)

        Returns:
            Output path
        """
        # Setup scene
        self.setup_scene()

        # Override frame range if specified
        if frame_start is not None:
            self.scene.frame_start = frame_start
        if frame_end is not None:
            self.scene.frame_end = frame_end

        # Set output path
        self.scene.render.filepath = output_path

        # Ensure output directory exists
        abs_path = bpy.path.abspath(output_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)

        # Render
        print(f"\nRendering frames {self.scene.frame_start}-{self.scene.frame_end}...")
        bpy.ops.render.render(animation=True)

        print(f"Animation saved to: {output_path}")
        return output_path

    def render_all_cameras(
        self,
        output_dir: str = "//output/",
        cameras: Optional[List[Camera]] = None
    ) -> List[str]:
        """
        Render from multiple cameras.

        Args:
            output_dir: Output directory
            cameras: List of cameras (all cameras if None)

        Returns:
            List of output paths
        """
        if cameras is None:
            cameras = [obj for obj in bpy.data.objects if obj.type == 'CAMERA']

        output_paths = []

        for camera in cameras:
            # Set active camera
            self.scene.camera = camera

            # Create output path
            cam_name = camera.name.replace(" ", "_")
            output_path = f"{output_dir}{cam_name}_"

            # Render
            self.render_animation(output_path)
            output_paths.append(output_path)

        return output_paths

    def create_playblast(
        self,
        output_path: str = "//output/playblast.mp4",
        viewport: bool = True
    ) -> str:
        """
        Create quick viewport playblast.

        Args:
            output_path: Output file path
            viewport: Use viewport render (faster)

        Returns:
            Path to playblast
        """
        # Use OpenGL render for speed
        if viewport:
            # Set preview settings
            self.scene.render.resolution_x = 1280
            self.scene.render.resolution_y = 720
            self.scene.render.filepath = output_path

            # OpenGL render
            bpy.ops.render.opengl(animation=True)
        else:
            # Quick render
            original_samples = self.scene.cycles.samples
            self.scene.cycles.samples = 16
            self.render_animation(output_path)
            self.scene.cycles.samples = original_samples

        print(f"Playblast saved to: {output_path}")
        return output_path

    def setup_render_layers(self) -> None:
        """Setup render layers for compositing flexibility."""
        scene = self.scene

        # Get or create render layers
        if not scene.view_layers:
            scene.view_layers.new("View Layer")

        view_layer = scene.view_layers[0]

        # Enable passes for compositing
        view_layer.use_pass_z = True
        view_layer.use_pass_mist = True
        view_layer.use_pass_normal = True
        view_layer.use_pass_vector = True
        view_layer.use_pass_uv = True
        view_layer.use_pass_object_index = True
        view_layer.use_pass_material_index = True

        # Emission and environment
        view_layer.use_pass_emit = True
        view_layer.use_pass_environment = True

        # Diffuse/Specular passes
        view_layer.use_pass_diffuse_direct = True
        view_layer.use_pass_diffuse_indirect = True
        view_layer.use_pass_glossy_direct = True
        view_layer.use_pass_glossy_indirect = True

        # Shadow and AO
        view_layer.use_pass_shadow = True
        view_layer.use_pass_ambient_occlusion = True


class RenderQueue:
    """
    Queue multiple renders for batch processing.

    Usage:
        queue = RenderQueue()
        queue.add("preview", "//output/preview_")
        queue.add("production", "//output/final_")
        queue.run_all()
    """

    def __init__(self):
        self.jobs: List[Dict[str, Any]] = []

    def add(
        self,
        preset: str,
        output_path: str,
        frame_range: Optional[Tuple[int, int]] = None,
        camera: Optional[str] = None
    ) -> None:
        """Add render job to queue."""
        self.jobs.append({
            "preset": preset,
            "output_path": output_path,
            "frame_range": frame_range,
            "camera": camera,
        })

    def run_all(self) -> List[str]:
        """Execute all render jobs."""
        results = []

        for i, job in enumerate(self.jobs):
            print(f"\n{'='*60}")
            print(f"Render Job {i+1}/{len(self.jobs)}: {job['preset']}")
            print(f"{'='*60}\n")

            pipeline = ChaseRenderPipeline.from_preset(job["preset"])
            pipeline.setup_scene()

            if job["camera"]:
                cam = bpy.data.objects.get(job["camera"])
                if cam and cam.type == 'CAMERA':
                    bpy.context.scene.camera = cam

            frame_start, frame_end = job["frame_range"] or (None, None)
            result = pipeline.render_animation(
                job["output_path"],
                frame_start,
                frame_end
            )
            results.append(result)

        return results


# Convenience functions
def quick_render(path: str = "//output/quick_") -> str:
    """Quick render current frame."""
    pipeline = ChaseRenderPipeline.from_preset("preview")
    return pipeline.quick_render(path)


def render_chase(
    output_path: str = "//output/chase_",
    preset: str = "standard"
) -> str:
    """Render chase animation."""
    pipeline = ChaseRenderPipeline.from_preset(preset)
    return pipeline.render_animation(output_path)


def create_playblast(path: str = "//output/playblast.mp4") -> str:
    """Create quick playblast."""
    pipeline = ChaseRenderPipeline.from_preset("preview")
    return pipeline.create_playblast(path)
