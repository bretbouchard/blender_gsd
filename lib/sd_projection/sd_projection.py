"""
SD Projection Mapping System - Stable Diffusion texture projection onto 3D geometry.

Creates the "Arcane" style painted-on effect where AI-generated textures
are projected onto buildings with controllable style blending and
drifting/slipping animation effects.

Architecture:
1. Capture depth/normal/canny passes from Blender camera view
2. Send to SD WebUI/ComfyUI with ControlNet conditioning
3. Generate styled textures maintaining 3D structure
4. Project generated textures back onto geometry
5. Animate texture drift/slipping independently of geometry

Usage:
    from lib.sd_projection import SDProjectionMapper, StyleConfig

    # Configure projection
    config = StyleConfig(
        style_models=["cyberpunk", "noir"],
        style_blend=0.7,  # 70% style A, 30% style B
        drift_enabled=True,
        drift_speed=0.1,
    )

    # Create projection mapper
    mapper = SDProjectionMapper(config)

    # Generate and project onto buildings
    result = mapper.project_onto_objects(
        camera=scene.camera,
        objects=buildings,
        prompt="neon lit cyberpunk city, rain wet streets",
    )
"""

from __future__ import annotations

import bpy
import mathutils
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import time
import subprocess
import tempfile

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from PIL import Image
    import numpy as np
    IMAGE_LIBS_AVAILABLE = True
except ImportError:
    IMAGE_LIBS_AVAILABLE = False


# =============================================================================
# ENUMS AND TYPES
# =============================================================================

class ControlNetType(Enum):
    """ControlNet conditioning types."""
    DEPTH = "depth"
    NORMAL = "normal"
    CANNY = "canny"
    POSE = "pose"
    SCRIBBLE = "scribble"
    SOFTEDGE = "softedge"
    LINEART = "lineart"
    MLSD = "mlsd"
    SEGMENTATION = "segmentation"


class ProjectionMode(Enum):
    """How to apply projected texture."""
    CAMERA_PROJECT = "camera_project"    # Project from camera view
    UV_REPLACE = "uv_replace"            # Replace UV texture
    UV_BLEND = "uv_blend"                # Blend with existing UV
    TRIPPY = "trippy"                    # Drifting/slipping effect


class SDBackend(Enum):
    """SD backend to use."""
    AUTO1111 = "auto1111"    # Stable Diffusion WebUI
    COMFYUI = "comfyui"      # ComfyUI
    LOCAL = "local"          # Local diffusers pipeline


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class StyleModel:
    """A style model/LoRA configuration."""
    name: str
    path: str = ""                     # Path to LoRA or checkpoint
    weight: float = 1.0
    trigger_words: List[str] = field(default_factory=list)
    is_lora: bool = True


@dataclass
class ControlNetConfig:
    """ControlNet conditioning configuration."""
    control_type: ControlNetType = ControlNetType.DEPTH
    model: str = "control_v11f1p_sd15_depth"
    weight: float = 1.0
    guidance_start: float = 0.0
    guidance_end: float = 1.0
    preprocessor: str = "depth_anything"
    # For canny
    canny_low: int = 100
    canny_high: int = 200


@dataclass
class StyleConfig:
    """Complete style/projection configuration."""
    # Style models (can blend multiple)
    style_models: List[StyleModel] = field(default_factory=list)

    # Blend between styles (0-1, controls mix of style_models[0] and style_models[1])
    style_blend: float = 0.5

    # ControlNet settings
    controlnets: List[ControlNetConfig] = field(default_factory=lambda: [
        ControlNetConfig(control_type=ControlNetType.DEPTH, weight=1.0),
        ControlNetConfig(control_type=ControlNetType.NORMAL, weight=0.5),
    ])

    # Projection settings
    projection_mode: ProjectionMode = ProjectionMode.TRIPPY
    projection_resolution: Tuple[int, int] = (2048, 2048)

    # Drift/slipping effect settings (flat fields for direct use)
    drift_enabled: bool = True
    drift_speed: float = 0.1           # UV drift speed (0-1)
    drift_direction: Tuple[float, float] = (1.0, 0.5)  # UV drift direction
    drift_noise_scale: float = 0.3     # Noise-based drift variation
    drift_wave_amplitude: float = 0.1  # Wave-like drift
    drift_wave_frequency: float = 2.0

    # Optional DriftConfig object (if provided, overrides flat drift fields)
    drift_config: Optional[Any] = None  # DriftConfig from style_blender

    # SD generation settings
    prompt: str = ""
    negative_prompt: str = "blurry, low quality, distorted"
    steps: int = 30
    cfg_scale: float = 7.0
    sampler: str = "DPM++ 2M Karras"
    seed: int = -1  # -1 = random

    # Backend settings
    backend: SDBackend = SDBackend.AUTO1111
    api_url: str = "http://127.0.0.1:7860"
    checkpoint: str = "v1-5-pruned-emaonly.safetensors"

    # Output settings
    output_dir: Path = field(default_factory=lambda: Path(tempfile.gettempdir()) / "sd_projection")
    cache_generations: bool = True

    def __post_init__(self):
        """Sync drift_config to flat fields if drift_config is provided."""
        if self.drift_config is not None:
            self.drift_enabled = self.drift_config.enabled
            self.drift_speed = self.drift_config.speed
            self.drift_direction = self.drift_config.direction
            if hasattr(self.drift_config, 'noise_strength'):
                self.drift_noise_scale = self.drift_config.noise_strength
            if hasattr(self.drift_config, 'wave_amplitude'):
                self.drift_wave_amplitude = self.drift_config.wave_amplitude
            if hasattr(self.drift_config, 'wave_frequency'):
                self.drift_wave_frequency = getattr(self.drift_config, 'wave_frequency', 2.0)


@dataclass
class ProjectionResult:
    """Result of a projection operation."""
    success: bool
    projected_objects: List[str] = field(default_factory=list)
    generated_texture_path: Optional[Path] = None
    material_name: str = ""
    generation_time: float = 0.0
    seed_used: int = 0
    error_message: str = ""


# =============================================================================
# PASS GENERATION
# =============================================================================

class PassGenerator:
    """Generate depth, normal, and other control passes from Blender."""

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_depth_pass(
        self,
        camera: bpy.types.Object,
        resolution: Tuple[int, int] = (1024, 1024),
        objects: Optional[List[bpy.types.Object]] = None
    ) -> Path:
        """
        Generate depth map from camera view.

        Args:
            camera: Camera to render from
            resolution: Output resolution
            objects: Optional list of objects to include

        Returns:
            Path to generated depth map
        """
        output_path = self.output_dir / "depth_pass.exr"

        # Store original settings
        original_resolution = (
            bpy.context.scene.render.resolution_x,
            bpy.context.scene.render.resolution_y
        )
        original_camera = bpy.context.scene.camera
        original_engine = bpy.context.scene.render.engine

        try:
            # Set up render settings
            bpy.context.scene.render.resolution_x = resolution[0]
            bpy.context.scene.render.resolution_y = resolution[1]
            bpy.context.scene.camera = camera
            bpy.context.scene.render.engine = 'CYCLES'
            bpy.context.scene.render.filepath = str(output_path)
            bpy.context.scene.render.image_settings.file_format = 'OPEN_EXR'
            bpy.context.scene.render.image_settings.color_depth = '32'

            # Enable depth pass
            bpy.context.scene.render.use_compositing = True
            bpy.context.scene.use_nodes = True

            tree = bpy.context.scene.node_tree
            tree.nodes.clear()

            # Create render layers node
            render_layers = tree.nodes.new('CompositorNodeRLayers')
            render_layers.layer = "View Layer"

            # Enable depth output
            bpy.context.scene.view_layers["View Layer"].use_pass_z = True

            # Create file output node
            file_output = tree.nodes.new('CompositorNodeOutputFile')
            file_output.base_path = str(self.output_dir)
            file_output.format.file_format = 'OPEN_EXR'
            file_output.format.color_depth = '32'
            file_output.file_slots[0].path = "depth_pass"

            # Link depth to output
            tree.links.new(render_layers.outputs['Depth'], file_output.inputs[0])

            # Render
            bpy.ops.render.render(write_still=True)

            # Convert EXR to PNG for SD
            depth_exr = self.output_dir / "depth_pass0001.exr"
            depth_png = self.output_dir / "depth_pass.png"

            if depth_exr.exists():
                self._convert_depth_to_png(depth_exr, depth_png)
                return depth_png

        finally:
            # Restore original settings
            bpy.context.scene.render.resolution_x = original_resolution[0]
            bpy.context.scene.render.resolution_y = original_resolution[1]
            bpy.context.scene.camera = original_camera
            bpy.context.scene.render.engine = original_engine

        return output_path

    def generate_normal_pass(
        self,
        camera: bpy.types.Object,
        resolution: Tuple[int, int] = (1024, 1024)
    ) -> Path:
        """Generate normal map from camera view."""
        output_path = self.output_dir / "normal_pass.png"

        # Store original settings
        original_engine = bpy.context.scene.render.engine
        original_resolution = (
            bpy.context.scene.render.resolution_x,
            bpy.context.scene.render.resolution_y
        )
        original_camera = bpy.context.scene.camera

        try:
            bpy.context.scene.render.engine = 'CYCLES'
            bpy.context.scene.render.resolution_x = resolution[0]
            bpy.context.scene.render.resolution_y = resolution[1]
            bpy.context.scene.camera = camera

            # Set up normal pass through compositing
            bpy.context.scene.use_nodes = True
            tree = bpy.context.scene.node_tree
            tree.nodes.clear()

            render_layers = tree.nodes.new('CompositorNodeRLayers')
            bpy.context.scene.view_layers["View Layer"].use_pass_normal = True

            # Create separate RGBA output for normal
            file_output = tree.nodes.new('CompositorNodeOutputFile')
            file_output.base_path = str(self.output_dir)
            file_output.format.file_format = 'PNG'
            file_output.format.color_mode = 'RGBA'
            file_output.file_slots[0].path = "normal_pass"

            # Link normal to output
            tree.links.new(render_layers.outputs['Normal'], file_output.inputs[0])

            bpy.ops.render.render(write_still=True)

            normal_file = self.output_dir / "normal_pass0001.png"
            if normal_file.exists():
                normal_file.rename(output_path)
                return output_path

        finally:
            bpy.context.scene.render.engine = original_engine
            bpy.context.scene.render.resolution_x = original_resolution[0]
            bpy.context.scene.render.resolution_y = original_resolution[1]
            bpy.context.scene.camera = original_camera

        return output_path

    def generate_canny_pass(
        self,
        camera: bpy.types.Object,
        resolution: Tuple[int, int] = (1024, 1024),
        low_threshold: int = 100,
        high_threshold: int = 200
    ) -> Path:
        """
        Generate edge detection (canny-style) pass.

        Uses Blender's freestyle or compositor edge detection.
        """
        output_path = self.output_dir / "canny_pass.png"

        # Store settings
        original_engine = bpy.context.scene.render.engine
        original_resolution = (
            bpy.context.scene.render.resolution_x,
            bpy.context.scene.render.resolution_y
        )
        original_camera = bpy.context.scene.camera
        original_freestyle = bpy.context.scene.render.use_freestyle

        try:
            bpy.context.scene.render.engine = 'BLENDER_EEVEE'  # Faster for line art
            bpy.context.scene.render.resolution_x = resolution[0]
            bpy.context.scene.render.resolution_y = resolution[1]
            bpy.context.scene.camera = camera

            # Enable freestyle for edge detection
            bpy.context.scene.render.use_freestyle = True
            freestyle = bpy.context.scene.view_layers["View Layer"].freestyle_settings

            # Configure freestyle lines
            if freestyle.linesets:
                lineset = freestyle.linesets[0]
            else:
                lineset = freestyle.linesets.new()

            lineset.select_by_visibility = True
            lineset.select_by_edge_types = True
            lineset.select_by_face_marks = False
            lineset.select_by_collection = False
            lineset.edge_type_negation = True
            lineset.edge_type_combination = True

            # Enable all edge types for comprehensive line detection
            for edge_type in ['SILHOUETTE', 'CREASE', 'BORDER', 'CONTOUR', 'SUGGESTIVE_CONTOUR', 'VALLEY', 'RIDGE']:
                if hasattr(lineset, f'edge_type_{edge_type.lower()}'):
                    setattr(lineset, f'edge_type_{edge_type.lower()}', True)

            # Set line style
            linestyle = lineset.linestyle
            linestyle.color = (1.0, 1.0, 1.0)  # White lines
            linestyle.thickness = 1.0

            # Render to file
            bpy.context.scene.render.filepath = str(output_path)
            bpy.context.scene.render.image_settings.file_format = 'PNG'
            bpy.context.scene.render.image_settings.color_mode = 'RGB'

            bpy.ops.render.render(write_still=True)

            return output_path

        finally:
            bpy.context.scene.render.engine = original_engine
            bpy.context.scene.render.resolution_x = original_resolution[0]
            bpy.context.scene.render.resolution_y = original_resolution[1]
            bpy.context.scene.camera = original_camera
            bpy.context.scene.render.use_freestyle = original_freestyle

    def _convert_depth_to_png(self, exr_path: Path, png_path: Path):
        """Convert depth EXR to normalized PNG."""
        if not IMAGE_LIBS_AVAILABLE:
            # Fallback: just copy
            import shutil
            shutil.copy(exr_path, png_path.with_suffix('.exr'))
            return

        # Load EXR
        import numpy as np
        from PIL import Image

        # OpenEXR loading would go here
        # For now, use Blender's built-in conversion
        pass


# =============================================================================
# SD GENERATION
# =============================================================================

class SDClient:
    """Client for Stable Diffusion backends."""

    def __init__(self, config: StyleConfig):
        self.config = config

    def generate_with_controlnet(
        self,
        prompt: str,
        negative_prompt: str,
        control_images: Dict[ControlNetType, Path],
        resolution: Tuple[int, int] = (1024, 1024),
        seed: int = -1
    ) -> Tuple[Path, int]:
        """
        Generate image using ControlNet conditioning.

        Args:
            prompt: Positive prompt
            negative_prompt: Negative prompt
            control_images: Dict mapping ControlNet type to image path
            resolution: Output resolution
            seed: Random seed (-1 for random)

        Returns:
            Tuple of (output_path, seed_used)
        """
        if self.config.backend == SDBackend.AUTO1111:
            return self._generate_auto1111(prompt, negative_prompt, control_images, resolution, seed)
        elif self.config.backend == SDBackend.COMFYUI:
            return self._generate_comfyui(prompt, negative_prompt, control_images, resolution, seed)
        else:
            raise NotImplementedError(f"Backend {self.config.backend} not implemented")

    def _generate_auto1111(
        self,
        prompt: str,
        negative_prompt: str,
        control_images: Dict[ControlNetType, Path],
        resolution: Tuple[int, int],
        seed: int
    ) -> Tuple[Path, int]:
        """Generate using Automatic1111 WebUI API."""
        if not REQUESTS_AVAILABLE:
            raise RuntimeError("requests library required for Auto1111 API")

        # Build ControlNet units
        controlnet_units = []
        for cn_config in self.config.controlnets:
            if cn_config.control_type in control_images:
                img_path = control_images[cn_config.control_type]
                img_b64 = self._image_to_base64(img_path)

                controlnet_units.append({
                    "input_image": img_b64,
                    "module": cn_config.preprocessor,
                    "model": cn_config.model,
                    "weight": cn_config.weight,
                    "guidance_start": cn_config.guidance_start,
                    "guidance_end": cn_config.guidance_end,
                })

        # Build prompt with style models
        full_prompt = prompt
        for style in self.config.style_models:
            if style.trigger_words:
                full_prompt = f"{full_prompt}, {', '.join(style.trigger_words)}"

        # API payload
        payload = {
            "prompt": full_prompt,
            "negative_prompt": negative_prompt,
            "steps": self.config.steps,
            "cfg_scale": self.config.cfg_scale,
            "sampler_name": self.config.sampler,
            "width": resolution[0],
            "height": resolution[1],
            "seed": seed if seed >= 0 else -1,
            "alwayson_scripts": {
                "controlnet": {
                    "enabled": True,
                    "module": "none",
                    "model": self.config.controlnets[0].model if self.config.controlnets else "None",
                    "weight": 1.0,
                    "image": "",
                    "resize_mode": 1,
                    "lowvram": False,
                    "processor_res": 512,
                    "threshold_a": 64,
                    "threshold_b": 64,
                    "guidance_start": 0.0,
                    "guidance_end": 1.0,
                }
            }
        }

        # Add LoRA if specified
        extra_networks = []
        for style in self.config.style_models:
            if style.is_lora and style.path:
                extra_networks.append(f"<lora:{style.name}:{style.weight}>")

        if extra_networks:
            payload["prompt"] = f"{payload['prompt']} {' '.join(extra_networks)}"

        # Call API
        response = requests.post(
            f"{self.config.api_url}/sdapi/v1/txt2img",
            json=payload,
            timeout=300
        )
        response.raise_for_status()

        result = response.json()

        # Save output
        import base64
        output_path = self.config.output_dir / f"sd_output_{int(time.time())}.png"
        img_data = base64.b64decode(result["images"][0].split(",", 1)[0])

        with open(output_path, "wb") as f:
            f.write(img_data)

        seed_used = result.get("info", {}).get("seed", seed)

        return output_path, seed_used

    def _generate_comfyui(
        self,
        prompt: str,
        negative_prompt: str,
        control_images: Dict[ControlNetType, Path],
        resolution: Tuple[int, int],
        seed: int
    ) -> Tuple[Path, int]:
        """Generate using ComfyUI API."""
        # ComfyUI uses a different workflow format
        # This would need to be implemented for full ComfyUI support
        raise NotImplementedError("ComfyUI backend not yet implemented")

    def _image_to_base64(self, image_path: Path) -> str:
        """Convert image to base64 string."""
        import base64

        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")


# =============================================================================
# PROJECTION MAPPER
# =============================================================================

class SDProjectionMapper:
    """
    Main class for SD-based texture projection.

    Handles the complete pipeline:
    1. Generate control passes (depth, normal, canny)
    2. Call SD with ControlNet
    3. Project generated texture onto geometry
    4. Set up drift/slipping animation
    """

    def __init__(self, config: StyleConfig):
        self.config = config
        self.pass_generator = PassGenerator(config.output_dir)
        self.sd_client = SDClient(config)

        # Ensure output directory exists
        config.output_dir.mkdir(parents=True, exist_ok=True)

    def project_onto_objects(
        self,
        camera: bpy.types.Object,
        objects: List[bpy.types.Object],
        prompt: Optional[str] = None,
        seed: int = -1
    ) -> ProjectionResult:
        """
        Project SD-generated texture onto objects.

        Args:
            camera: Camera to project from
            objects: Objects to project onto
            prompt: Override prompt (uses config.prompt if None)
            seed: Random seed (-1 for random)

        Returns:
            ProjectionResult with success status and details
        """
        start_time = time.time()
        result = ProjectionResult(success=False)

        try:
            # Use config prompt if not overridden
            if prompt is None:
                prompt = self.config.prompt

            # Calculate resolution
            resolution = self.config.projection_resolution

            # Generate control passes
            print("Generating control passes...")
            control_images = {}

            # Always generate depth
            depth_path = self.pass_generator.generate_depth_pass(camera, resolution)
            control_images[ControlNetType.DEPTH] = depth_path

            # Generate normal if configured
            for cn_config in self.config.controlnets:
                if cn_config.control_type == ControlNetType.NORMAL and cn_config.weight > 0:
                    normal_path = self.pass_generator.generate_normal_pass(camera, resolution)
                    control_images[ControlNetType.NORMAL] = normal_path
                    break

            # Generate canny if configured
            for cn_config in self.config.controlnets:
                if cn_config.control_type == ControlNetType.CANNY and cn_config.weight > 0:
                    canny_path = self.pass_generator.generate_canny_pass(
                        camera, resolution,
                        cn_config.canny_low, cn_config.canny_high
                    )
                    control_images[ControlNetType.CANNY] = canny_path
                    break

            # Generate SD texture
            print("Generating SD texture...")
            texture_path, seed_used = self.sd_client.generate_with_controlnet(
                prompt=prompt,
                negative_prompt=self.config.negative_prompt,
                control_images=control_images,
                resolution=resolution,
                seed=seed
            )

            result.generated_texture_path = texture_path
            result.seed_used = seed_used

            # Create material and project onto objects
            print("Projecting texture onto objects...")
            for obj in objects:
                self._apply_projected_material(obj, texture_path, camera)
                result.projected_objects.append(obj.name)

            result.success = True
            result.generation_time = time.time() - start_time

            print(f"Projection complete in {result.generation_time:.1f}s")

        except Exception as e:
            result.error_message = str(e)
            print(f"Projection failed: {e}")

        return result

    def _apply_projected_material(
        self,
        obj: bpy.types.Object,
        texture_path: Path,
        camera: bpy.types.Object
    ):
        """Apply projected texture material to object."""
        # Create new material
        mat_name = f"{obj.name}_SD_Projected"
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        # Create node layout
        output = nodes.new('ShaderNodeOutputMaterial')
        output.location = (600, 0)

        principled = nodes.new('ShaderNodeBsdfPrincipled')
        principled.location = (300, 0)

        # Texture coordinate for camera projection
        tex_coord = nodes.new('ShaderNodeTexCoord')
        tex_coord.location = (-800, 0)

        # Camera data for projection
        camera_data = nodes.new('ShaderNodeCamera')
        camera_data.location = (-800, -200)

        # Vector transform for camera space
        vec_transform = nodes.new('ShaderNodeVectorTransform')
        vec_transform.location = (-600, 0)
        vec_transform.vector_type = 'POINT'
        vec_transform.convert_from = 'WORLD'
        vec_transform.convert_to = 'CAMERA'

        # Load texture
        tex_image = nodes.new('ShaderNodeTexImage')
        tex_image.location = (-300, 0)

        # Load the generated texture
        try:
            image = bpy.data.images.load(str(texture_path), check_existing=True)
            tex_image.image = image
        except RuntimeError:
            # Create placeholder
            image = bpy.data.images.new("placeholder", 1024, 1024)
            tex_image.image = image

        # UV Map node for fallback
        uv_map = nodes.new('ShaderNodeUVMap')
        uv_map.location = (-600, 200)

        # Mix vector for projection vs UV
        mix_vec = nodes.new('ShaderNodeMix')
        mix_vec.data_type = 'VECTOR'
        mix_vec.location = (-100, 100)

        # Drift animation if enabled
        if self.config.drift_enabled and self.config.projection_mode == ProjectionMode.TRIPPY:
            self._add_drift_nodes(nodes, links, tex_coord, mix_vec)

        # Connect nodes
        links.new(tex_coord.outputs['Camera'], vec_transform.inputs['Vector'])
        links.new(vec_transform.outputs['Vector'], tex_image.inputs['Vector'])
        links.new(tex_image.outputs['Color'], principled.inputs['Base Color'])
        links.new(tex_image.outputs['Alpha'], principled.inputs['Alpha'])
        links.new(principled.outputs['BSDF'], output.inputs['Surface'])

        # Assign material to object
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)

        result.material_name = mat_name

    def _add_drift_nodes(
        self,
        nodes,
        links,
        tex_coord: bpy.types.Node,
        mix_vec: bpy.types.Node
    ):
        """Add UV drift/slipping animation nodes."""
        # Create animated offset
        # UV = UV + (drift_direction * drift_speed * frame)

        # Frame input
        frame_node = nodes.new('ShaderNodeValue')
        frame_node.location = (-1000, -400)
        # Driver will be added for frame

        # Multiply by speed
        speed_mult = nodes.new('ShaderNodeMath')
        speed_mult.operation = 'MULTIPLY'
        speed_mult.location = (-800, -400)
        speed_mult.inputs[1].default_value = self.config.drift_speed

        # Drift direction
        direction = nodes.new('ShaderNodeCombineXYZ')
        direction.location = (-600, -400)
        direction.inputs['X'].default_value = self.config.drift_direction[0]
        direction.inputs['Y'].default_value = self.config.drift_direction[1]
        direction.inputs['Z'].default_value = 0.0

        # Multiply speed by direction
        vec_mult = nodes.new('ShaderNodeVectorMath')
        vec_mult.operation = 'MULTIPLY'
        vec_mult.location = (-400, -300)

        # Add to UV
        add_vec = nodes.new('ShaderNodeVectorMath')
        add_vec.operation = 'ADD'
        add_vec.location = (-200, 0)

        # Noise for variation
        noise_tex = nodes.new('ShaderNodeTexNoise')
        noise_tex.location = (-600, -600)
        noise_tex.inputs['Scale'].default_value = self.config.drift_noise_scale * 10
        noise_tex.inputs['Detail'].default_value = 2

        # Wave for undulation
        wave_tex = nodes.new('ShaderNodeTexWave')
        wave_tex.location = (-600, -800)
        wave_tex.inputs['Scale'].default_value = self.config.drift_wave_frequency

        # Links
        links.new(tex_coord.outputs['UV'], add_vec.inputs[0])
        links.new(add_vec.outputs['Vector'], mix_vec.inputs[1])


def create_projection_mapper(
    style_models: List[str] = None,
    prompt: str = "",
    api_url: str = "http://127.0.0.1:7860",
    output_dir: Path = None
) -> SDProjectionMapper:
    """
    Quick function to create a projection mapper.

    Args:
        style_models: List of style/LoRA names
        prompt: Default prompt
        api_url: SD WebUI API URL
        output_dir: Output directory for generated textures

    Returns:
        Configured SDProjectionMapper
    """
    styles = []
    if style_models:
        for name in style_models:
            styles.append(StyleModel(name=name))

    config = StyleConfig(
        style_models=styles,
        prompt=prompt,
        api_url=api_url,
        output_dir=output_dir or Path(tempfile.gettempdir()) / "sd_projection",
    )

    return SDProjectionMapper(config)


# Convenience exports
__all__ = [
    "SDProjectionMapper",
    "StyleConfig",
    "StyleModel",
    "ControlNetConfig",
    "ControlNetType",
    "ProjectionMode",
    "SDBackend",
    "ProjectionResult",
    "PassGenerator",
    "SDClient",
    "create_projection_mapper",
]
