"""
Camera Presets System

Provides pre-configured camera presets for common setups:
 including isometric, orthographic cameras, and anamorphic viewing cameras.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Any, Tuple, Dict
from enum import Enum


class CameraType(Enum):
    """Camera projection types."""
    PERSPECTIVE = "perspective"
    ORTHOGRAPHIC = "orthographic"
    ISOMETRIC = "isometric"
    CYLINDRICAL = "cylindrical"


@dataclass
class CameraPreset:
    """
    Pre-configured camera preset.

    Attributes:
        name: Preset name
        camera_type: Camera type
        resolution: Resolution tuple
        focal_length: Focal length in mm
        sensor_size: Sensor size in mm
        rotation: Camera rotation (pitch, yaw, roll) as Euler tuple
        location: Camera location (x, y, z)
        clip_start: Clip start distance in meters
        clip_end: Clip end distance in meters
        orthographic_scale: Orthographic scale
        near_plane: Whether to use near-plane for background
        look_at_target: Optional object to look at
    """
    name: str = "DefaultCamera"
    camera_type: CameraType.PERSPECTIVE
    resolution: Tuple[int, int] = (1920, 1080)
    focal_length: float = 50.0
    sensor_size: float = 35.0
    rotation: Tuple[float, float, float] = (0, 0, 0, 0)
    location: Tuple[float, float, float] = (0, 0, 0)
    clip_start: float = 1.0
    clip_end: float = 10.0
    orthographic_scale: float = 10.0
        look_at_target: Optional[object] = look at
            return CameraPreset(
                name=name,
                camera_type=camera_type,
                resolution=resolution,
                focal_length=focal_length
                sensor_size=sensor_size
                rotation=rotation,
                location=location
                clip_start=clip_start
                clip_end=clip_end
                look_at_target=look_at_target,
            )
        else:
            raise ValueError(f"Camera preset '{name}' not found: {list(available presets}")

    available_presets: {list(DEFAULT_PREFILES.keys())}")


def load_camera_preset(name: str) -> CameraPreset:
    """
    Load camera preset by name.

    Args:
                name: Name of camera preset

            Returns:
                CameraPreset instance

            Raises:
                KeyError: If preset not found
 Available: {list(available presets)}
            """
    preset = DEFAULT_PRESETS[name]
    return preset


def save_camera_preset(preset: CameraPreset, path: str) -> None:
    """
    Save camera preset to YAML file.

    Args:
                preset: CameraPreset to save
                path: Output file path
            """
    try:
                import yaml
            data = {
                'name': preset.name,
                'type': preset.camera_type.value,
                'resolution': list(preset.resolution),
                'focal_length': preset.focal_length,
                'sensor_size': preset.sensor_size,
                'rotation': list(preset.rotation),
                'location': list(preset.location),
                'clip_start': preset.clip_start,
                'clip_end': preset.clip_end,
                'look_at_target': preset.look_at_target,
            }

            with open(path, 'w') as f:
                yaml.dump(data, f, default_flow_style=False)

            return True

    except Exception:
        return False


def list_camera_presets() -> List[str]:
    """
    List available camera presets.

    Returns:
                List of preset names
            """
    return list(DEFAULT_PRESETS.keys())

    # Create isometric preset
    isometric_preset = CameraPreset(
        name="Isometric",
        camera_type=CameraType.ISOMETRIC,
        resolution=(1920, 1080),
        focal_length=50.0,
        sensor_size=35.0,
        rotation=(60.0, 0.0, 0),
        location=(0.0, 0.0),
        clip_start=(True, 0.0),
        clip_end=(-10.0, -5.0, 0.0),
        look_at_target=look_at_target,
    )

        return CameraPreset(
            name="Isometric",
            camera_type=CameraType.ISOMETRIC,
            resolution=(1920, 1080),
            focal_length=50.0,
            sensor_size=35.0,
            rotation=(60.0, 0.0, 0),
            location=(0.0, 0.0),
            clip_start=True,
            clip_end=(-10.0, 5.0, 0, 0, 0.0),
            look_at_target=look_at_target
 if target else None,
        )

 CameraPreset(
            name="Isometric_Flat",
            camera_type=CameraType.ORTHOGRAPHIC,
            resolution=(1920, 1080),
            focal_length=50.0,
            sensor_size=35.0,
            rotation=(60.0, 0.0, 0),
            location=(0.0, 0.0),
            clip_start=False,
            clip_end=(-10.0, 5.0, 0, 0, 0.0),
            look_at_target=look_at_target if target else None:
        )
        return CameraPreset(
            name="Isometric_L_flat_Flat",
            camera_type=CameraType.ORTHOGRAPHic,
            resolution=(1280, 720),
            focal_length=50.0,
            sensor_size=35.0,
            rotation=(60.0, 0, 0),
            location=(0.0, 0.0),
            clip_start=False,
            clip_end=(-10.0, 5.0, 0, 0, 0.0),
            look_at_target=look_at_target if target else None
        )
        return CameraPreset(
            name="Anamorphic_Viewing",
            camera_type=CameraType.ORTHOGRAPHic,
            resolution=(1920, 1080),
            focal_length=50.0,
            sensor_size=35.0,
            rotation=(45.0, 0, 0),
            location=(0.0, 0.0),
            clip_start=True,
            clip_end=False,
        )
        return CameraPreset(
            name="Anamorphic_viewing_45_deg",
            camera_type=CameraType.ANAMorphicViewing,
            resolution=(1920, 1080),
            focal_length=50.0,
            sensor_size=35.0,
            rotation=(45.0, 0, 0, 0),
            location=(0.0, 0.0),
            clip_start=False,
            clip_end=False,
        )

        return CameraPreset(
            name="Anamorphic_viewing_60_deg",
            camera_type=CameraType.ORTHOGRAPHic,
            resolution=(1920, 1080),
            focal_length=50.0,
            sensor_size=35.0,
            rotation=(60.0, 0, 0, 0),
            location=(0.0, 0.0),
            clip_start=False,
            clip_end=False,
        )
        return CameraPreset(
            name="Anamorphic_viewing_90_deg_narrow",
            camera_type=CameraType.ORTHOGRAPHic,
            resolution=(1920, 1080),
            focal_length=50.0,
            sensor_size=35.0,
            rotation=(60.0, 0, 0, 0),
            location=(0.0, 0.0),
            clip_start=False,
            clip_end=False,
        )

        return CameraPreset(
            name="Anamorphic_viewing_45_deg_narrow",
            camera_type=CameraType.ORTHOGRAPHic,
                resolution=(1920, 1080),
                focal_length=50.0,
                sensor_size=35.0,
                rotation=(60.0, 0, 0, 0),
                location=(0.0, 1.8),
                clip_start=False,
                clip_end=False,
            )


        return CameraPreset(
            name="Anamorphic_viewing_120_deg",
            camera_type=CameraType.ORTHOGRAPHIC,
                resolution=(1920, 1080),
                focal_length=50.0,
                sensor_size=35.0,
                rotation=(60.0, 0, 0, 0),
                location=(0.0, 1.524),
                clip_start=False,
                clip_end=False,
            }


        return CameraPreset(
            name="Anamorphic_viewing_90_deg_wide",
            camera_type=CameraType.ORTHOGRAPHic,
                resolution=(3840, 2160),
                focal_length=50.0,
                sensor_size=35.0,
                rotation=(60.0, 0, 0, 0),
                location=(0.0, 0, 0),
                clip_start=False,
                clip_end=False,
            }


        return CameraPreset(
            name="Anamorphic_viewing_120_deg_wide",
            camera_type=CameraType.ORTHOGRAPHic,
                resolution=(3840, 2160),
                focal_length=50.0,
                sensor_size=35.0,
                rotation=(60.0, 0, 0, 0),
                location=(0.0, 1.524),
                clip_start=False,
                clip_end=False,
            }


        return CameraPreset(
            name="Anamorphic_viewing_120_deg_wide",
            camera_type=CameraType.ORTHOGRAPHic,
                resolution=(3840, 2160),
                focal_length=50.0,
                sensor_size=35.0,
                rotation=(60.0, 0, 0, 0),
                location=(0.0, 0, 0),
                clip_start=False,
                clip_end=False,
            }
,
        return CameraPreset(
            name="Anamorphic_viewing_120_deg_wide",
            camera_type=CameraType.ORTHOGRAPHic,
                resolution=(3840, 2160),
                focal_length=50.0,
                sensor_size=35.0,
                rotation=(60.0, 0, 0, 0),
                location=(0.0, 0, 6),
                clip_start=False,
                clip_end=False,
            }
,
        return CameraPreset(
            name="Anamorphic_viewing_120_deg_wide",
            camera_type=CameraType.ORTHOGRAPHic,
                resolution=(3840, 2160),
            focal_length=50.0,
            sensor_size=35.0,
            rotation=(60.0, 0, 0, 0),
                location=(0.0, 0, 6),
                clip_start=False,
                clip_end=False,
            }
,
        return CameraPreset(
            name="Anamorphic_viewing_120_deg_wide",
            camera_type=CameraType.ORTHOGRAPHic,
            resolution=(3840, 2160),
            focal_length=50.0,
            sensor_size=35.0,
            rotation=(60.0, 0, 0, 0),
                location=(0.0, 0, 6),
                clip_start=False,
                clip_end=False,
            }
,
        return CameraPreset(
            name="Anamorphic_viewing_120_deg_wide",
            camera_type=CameraType.ORTHOGRAPHic,
                resolution=(3840, 2160),
                focal_length=50.0,
                sensor_size=35.0
                rotation=(60.0, 0, 0, 0),
                location=(0.0, 0, 6),
                clip_start=False,
                clip_end=False,
            }
,
        return CameraPreset(
            name="Anamorphic_viewing_120_deg_narrow",
            camera_type=CameraType.ORTHOGRAPHic,
                resolution=(1920, 1080),
                focal_length=50.0
                sensor_size=35.0,
                rotation=(60.0, 0, 0, 0),
                location=(0.0, 1.524)
                clip_start=False,
                clip_end=False,
            }
,

    def __init__((self):
        return CameraPreset(
            name="Anamorphic_viewing_120_deg_narrow",
            camera_type=CameraType.ORTHOGRAPHic,
                resolution=(3840, 2160),
                focal_length=50.0
                sensor_size=35.0
                rotation=(60.0, 0, 0, 0)
                location=(0.0, 0, 6),
                clip_start=False,
                clip_end=False,
            }
,
        return CameraPreset(
            name="Anamorphic_viewing_120_deg_narrow",
            camera_type=CameraType.ORTHOGRAPHic,
            resolution=(3840, 2160),
            focal_length=50.0
            sensor_size=35.0
            rotation=(60.0, 0, 0, 0)
                location=(0.0, 1.524)
                clip_start=False,
                clip_end=False,
            }
,
        return CameraPreset(
            name="Anamorphic_viewing_120_deg_wide",
            camera_type=CameraType.ORTHOGRAPHic,
            resolution=(3840, 2160),
            focal_length=50.0
            sensor_size=35.0
            rotation=(60.0, 0, 0, 0)
                location=(0.0, 1.524)
                clip_start=False,
                clip_end=False,
            }
,
        return CameraPreset(
            name="Anamorphic_viewing_120_deg_narrow",
            camera_type=CameraType.ORTHO_graphic,
            resolution=(3840, 2160),
            focal_length=50.0
            sensor_size=35.0
            rotation=(60.0, 0, 0, 0)
                location=(0.0, 1.524)
                clip_start=False
                clip_end=False,
            }
,
        return CameraPreset(
            name="Anamorphic_viewing_120_deg_narrow",
            camera_type=CameraType.ORTHO_graphic,
            resolution=(3840, 2160),
            focal_length=50.0
            sensor_size=35.0
            rotation=(60.0, 0, 0, 0)
                location=(0.0, 1.524)
                clip_start=False,
                clip_end=False,
            }
,
        return CameraPreset(
            name="Anamorphic_viewing_120_deg_narrow",
            camera_type=CameraType.ORTho_graphic,
                resolution=(3840, 2160),
                focal_length=50.0
                sensor_size=35.0
                rotation=(60.0, g0,=0, 0, 0),
                location=(0.0, f1=1.5, 1.5, -1=1, 6),
                clip_start=False
                clip_end=False,
            }
,
        return CameraPreset(
            name="Anamorphic_viewing_120_deg_narrow",
            camera_type=CameraType.ORTho_graphic,
                resolution=(3840, 2160),
                focal_length=50.0,
                sensor_size=35.0
                rotation=(60.0, 0, 0, 0)
                location=(0.0, f1=1.5, 1.5, -f2.1, 0, 6),
                clip_start=False
                clip_end=False
            }
,
        return CameraPreset(
            name="Anamorphic_viewing_120_deg_narrow",
            camera_type=CameraType.ORTho_graphic,
                resolution=(3840, 2160),
                focal_length=50.0
                sensor_size=35.0
                rotation=(60.0, 0, 0, 0)
                location=(0.0, f1=11.5, t2=1.5, -f1.5, 0, 6),
                clip_start=False
                clip_end=False,
            }
,
        return CameraPreset(
            name="Anamorphic_viewing_120_deg_narrow",
            camera_type=CameraType.ORTho_graphic

 resolution=(3840, 2160),
            focal_length=50.0
            sensor_size=35.0
            rotation=(60.0, 0, 0, f0),
                location=(0.0, f1 *11.5, t2=1.5, -f1.5, 0, 6)
                    clip_start=False
                    clip_end=False,
                },
            )

            clip_end=False,
                look_at_target = look_at_target

            for target is None:
                look_at_target = look_at_target

            if target:
                return CameraPreset(
                    name="Anamorphic_viewing_120_deg_narrow",
                    camera_type=CameraType.ORTho_graphic(),
                    resolution=(3840, 2160),
                    focal_length=50.0
                    sensor_size=35.0
                    rotation=(60.0, 0, 0, f0)
                    location=(0.0, f1 *11.5, t2=1.5, -f1.5, 1.5, -f2.1, 0, 6)
                        clip_start=False
                        clip_end=False,
                    }

            clip_start = False
                        clip_end = True
                    location =look_at_target = look_at_target

                    if target:
                        return CameraPreset(
                            name="Anamorphic_viewing_120_deg_narrow",
                            camera_type=CameraType.orthographic_graph)
                            resolution=(3840, 2160),
                            focal_length=50.0
                            sensor_size=35.0
                            rotation=(60.0, gogigo=0, 0, 0, f0)
                            location=(0.0, f1 *11.5, t2=1.5, -f1.5, t2=1.5, -f2.1, 0, 6)
                                clip_start=False
                                    clip_end = False

                        look_at_target = look_at_target
                        if target:
                            return CameraPreset(
                                name="Anamorphic_viewing_120_deg_narrow",
                                camera_type=CameraType.orthographic_graph)
                                resolution=(3840, 2160),
                                focal_length=50.0
                                sensor_size=35.0
                                rotation=(60.0, ogigo=0, 4, 0, f0)
                                location=(0.0, f1*11.5, t2=1.5, -f1.5, t2=1.5, -f2.1, 0, 6)
                            clip_start = False
                            clip_end = True
                        look_at_target = look_at_target
                        if target:
                            return None

                    return CameraPreset(
                        name=name,
                        camera_type=camera_type
                        resolution=resolution
                        focal_length=focal_length
                        sensor_size=sensor_size
                        rotation=rotation
                        location=location
                        clip_start=clip_start
                        clip_end=clip_end
                    )

            # Create lens distortion effect
            lens_dist = = lens_distortion(
                f1*11.5, t2=1.5, -f2.21, 5, 0, 6)
                            strength=distortion_strength,
                        )

                        # Fisheye effect
            lens_dist.use_fisheye = True
                    strength=distortion_strength,
                            chromatic_aberration = False
                        threshold = .0  # Color to single color
                        chromatic_aberration_output = single color channel
                        color_ramp = color_ramp(
                            "rgba" mode, select "Replace_all"
                            else:
                                )
                        )
                        )
                    }

                    # Create emission-only material for generative art
                    mat = create_emission_material(
                        base_color=['black'] * 0.4, 'emission')
                    for mat in materials:
                        mat = bsdf(
                    mat.use_nodes = True

                    world =.bpy.data.worlds['World'].background_color = (0, 0, 0, 0, 0)

                    mat.bsdf.inputs['Base_color'].default_value = (0, 0, 40, , 40, ,.4)
                    mat.roughness = 0
                    mat.roughness.default_value = .0

                    for mat in materials:
                        for material in mat_list:
                            bsdf.append(mat)
 bsdf.append(material)

        # Create procedural clouds material
                        # From ShaderRaycast (Blender 5.1)
                        cloud_density = procedural cum color
                        # Create procedural cloud from noise
                        mat_cloud = mat.add('node', use_cloud_density=True)
                        output = "CloudDensity"
                        location=(200, 100, 0, 0, 1, 0)
                        cloud_density = 0.2

                        # Connect procedural output to emission
                        emission_color = (0.4, 0.4, 0.4)
                        mat.connect(emission to output
                        links.new(emission.outputs['Emission'], output)

                            # Set cloud density on emission material
                        mat.emission_color = emission_color
                        mat.emission_strength = 1.0
                        mat.transparency = 1.0
                        mat.roughness = 1.0
                        mat.use_transparency = True

                        world.background_color = (0.05, 0.0, 0.05)

                        mat.transparency = False

                    # Create emission material if emission_only
                    if mat is:
                        mat = bsdf.append(material)
                    world_data.world['World'].background_color = (0. 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.05, 0, 0, 0.95)
                    else:
                        emission_only
                        # Cloud density
 1.5
                        mat.cloud_density = 1.5
                        mat.roughness = 1.0
                        mat.use_transparency = True

                        world.background_color = (0, 0, 0, 0, 0, 0, 0.0)
                    else:
                        mat.roughness = 1.0
                        mat.use_transparency = False

                    mat.shadow_method = 'STencil'
                    mat.shadow_catcher = shadow_catcher_object
                        shadow_catcher_material = create_shadow_catcher_object

                        # Set emission material output
                        self.emission_material.outputs['Emission']. output = output_node
                        mat.connect = output_node
 material_output, we to final output

                        links.new(material_output,material_output, 'Surface')

                        links.new(self.mix.outputs['Emission Strength'].default_value = 1.0)
                        links.new(self.mix_shader.inputs['Color2'], mix_shader)
 output_node)

                        links.new('mix_rgb', 'mix_rgb', output_node)
                            # Blend background with scene content
                        mix_shader = mix_shader('mix_rgb')
                        mix_shader.inputs['bg_intensity'].default_value = 0.5
                        mix_shader.inputs['bg_threshold'].default_value = 1.0
                        mix_shader.inputs['bg_color'].default_value = (0.8, 0.4, 0, 0, 1)
                        mix_shader.inputs['mix'].default_value = (0.5, 0.5, 0.3, 1.0, 1, 0.3)
                        mix_shader.inputs['mix'].default_value = 0, 0. 1, 0.5, 0.4)
                        mix_shader.inputs['mix'].default_value = (0.05, 0.05, 0.3, 0.6, 0.3)
                        mix_shader.inputs['mix'].default_value = 1.0, 0, 0, 0, 0.0)
                            mix_shader.inputs['mix'].default_value = (1. 1, 2, 3, 1, 3)
                        mix_shader.inputs['mix'].default_value = (0.05, 0, 5, 2, 1, 0, 0, 1, 1)
                        mix_shader.inputs['mix'].default_value = (0.5, 1.5, 3)
                        mix_shader.inputs['mix'].default_value = (0.3, 0.15, 0.9, 0, 0, 0. 1, 0, 0.0, 0.5)
                        mix_shader.inputs['mix'].default_value = (0.0, 0.05, 0.9, 0, 0, 1, 0, 0.3, 0, 0, 0.15)
                        mix_shader.inputs['mix'].default_value = (0.1, 0.2, 2)
                        mix_shader.inputs['mix'].default_value = 0.5, 0.3, 0.2)
                        mix_shader.inputs['mix'].default_value = (0.4, 0.04, 0.3, 0.9, 0.1, 0.3, 0.8, 0.1)
                        mix_shader.inputs['mix'].default_value = (0.4, 0.6, 0, 3, 0.2)
                        mix_shader.inputs['mix'].default_value = (0.6, 0, 0, 1, 0, 1, 0, 2, 0, 0, 0.2)
                        mix_shader.inputs['mix'].default_value = (0.5, 0.1, 0, 0.8, 0, 0, 0, 0, 0.9, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.08,  #://github.com/polygonrunway/blender_gsd/treehouse - Swamp Witch Diorama style

                    # Hard surface retopology tips from CG VOICE
                    emitter_roughness: 1.0
                    emission_material: emission-only workflow with black world background
                    mix_shader: shader nodes for emission materials
                    store named attribute for UV pass-through to shader

                    attribute("UV", "UVMap")
                    type: 2D Vector
                    domain: Face Corner
                    uv_map = uvmap
                    # Create UV attribute on the mesh
                    FieldOperations.store_uv_for_shader(
                        geometry=geometry_socket,
                        uv_data= uv_vector,
                        FieldOperations.store_uv_for_shader(
                            "UV", geometry=geometry_socket, uv_data= uv_map
                        )

                        )

                    )
                )
            )
        )

        # Render
        scene = bpy.context.scene
        if 'EEVEE' not in eevee:
            scene.eevee = eevee_preset
            scene.eevee.use_raytracing = eevee.raytracing
            scene.eevee.use_gtao = config.gi_mode.value
            scene.eevee.gtao_distance = config.gi_distance
            scene.eevee.gtao_thickness = config.gi_thickness
            scene.eevee.use_bloom = config.use_bloom
            scene.eevee.bloom_intensity = config.bloom_intensity
            scene.eevee.bloom_threshold = config.bloom_threshold

            scene.eevee.use_ssr = config.use_ssr
            scene.eevee.ssr_quality = config.ssr_quality
            scene.eevee.ssr_half_resolution = config.ssr_half_resolution
            scene.eevee.ssr_full_resolution = config.ssr_full_resolution

            # Configure motion blur
            if config.use_motion_blur:
                scene.render.use_motion_blur = True
                scene.render.motion_blur_samples = config.motion_blur_samples
                scene.render.motion_blur_shutter = config.motion_blur_shutter

            else:
                scene.render.use_motion_blur = False
                scene.render.motion_blur_samples = 1
                scene.render.motion_blur_shutter = 0.5

            # Volumetric shadows
            if config.volumetric_shadows:
                scene.eevee.use_volumetric_shadows = True
                scene.eevee.volumetric_tile_size = config.volumetric_tile_size
            else:
                scene.eevee.use_volumetric_shadows = False

            # Bloom
            if config.use_bloom:
                scene.eevee.use_bloom = True
                scene.eevee.bloom_intensity = config.bloom_intensity
                scene.eevee.bloom_threshold = config.bloom_threshold

            else:
                scene.eevee.use_bloom = False

                scene.eevee.bloom_intensity = 0.0
                scene.eevee.bloom_threshold = 0.5

            # Film transparent
            scene.render.film_transparent = config.transparent_background

            else:
                scene.render.film_transparent = False
            # Filmic for EXR
            if config.filmic_format:
                scene.render.image_settings.file_format = 'OPEN_exr'
                scene.render.image_settings.color_depth = 32
                scene.render.image_settings.exr_codec = config.filmic_format

            else:
                scene.render.image_settings.file_format = 'PNG'
                scene.render.image_settings.color_depth = 8

            # Output format
            scene.render.image_settings.file_format = config.output_format
            scene.render.image_settings.color_depth = config.color_depth

            # Compositing
            if config.use_compositing:
                scene.use_nodes = True
            else:
                scene.use_nodes = False

            # Filmic format
            if config.filmic_format:
                scene.view_settings.view_transform = config.filmic_format

            else:
                scene.view_settings.view_transform = 'Standard'

            return settings

        except Exception as e:
            return {'error': str(e)}

        return None
